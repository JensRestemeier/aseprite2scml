import sys
import os
import argparse
from PIL import Image
import xml.etree.ElementTree as ET

# import aseprite from the git module
sys.path.insert(1, r'py_aseprite')
import aseprite

def convertAnim(ase_path, scml_path, ofs_x=0, ofs_y=0):
    scml_dir = os.path.dirname(scml_path)
    scml_name,_ = os.path.splitext(os.path.basename(scml_path))

    with open(ase_path, 'rb') as f:
        parsed_file = aseprite.AsepriteFile(f.read())
        
    spriter_data = ET.Element("spriter_data", scml_version="1.0", generator="BrashMonkey Spriter", generator_version="r11", pixel_mode="1")

    tags = []
    layers = {}
    layer_alpha = {}
    folders = {}
    frame_file = {}
    anim_layers = {}

    # extract metadata
    for frame_index,frame in enumerate(parsed_file.frames):
        for chunk in frame.chunks:
            if type(chunk) == aseprite.chunks.LayerChunk:
                layers[chunk.layer_index] = chunk.name
                if (chunk.flags & 1) > 0:
                    alpha = chunk.opacity
                else:
                    alpha = 0
                layer_alpha[chunk.layer_index] = alpha
            elif type(chunk) == aseprite.chunks.FrameTagsChunk:
                for tag in chunk.tags:
                    tags.append((tag["name"], tag["loop"], tag["from"], tag["to"]))
            elif type(chunk) == aseprite.chunks.PaletteChunk:
                pass

    # build animation names:
    frame_names = ["Anim" for x in range(len(parsed_file.frames))]
    for _name,_,_from, _to in tags:
        for i in range(_from, _to+1):
            frame_names[i] = _name

    anim_name = frame_names[0]
    anim_names = set([anim_name])
    frame_names_new = [anim_name]
    for i in range(1, len(frame_names)):
        if frame_names[i] != frame_names[i-1]:
            anim_name = frame_names[i]
            count = 1
            while anim_name in anim_names:
                anim_name = "%s%i" % (frame_names[i], count)
                count += 1
            anim_names.add(anim_name)
        frame_names_new.append(anim_name)

    frame_names = frame_names_new
    del frame_names_new

    # extract images
    frame_count = {}
    for frame_index,frame in enumerate(parsed_file.frames):
        for chunk in frame.chunks:
            if type(chunk) == aseprite.chunks.CelChunk:
                anim_name = frame_names[frame_index]
                try: 
                    folder = folders[anim_name]
                except KeyError:
                    folder = ET.SubElement(spriter_data, "folder", id=str(len(folders)), name=anim_name)
                    folders[anim_name] = folder

                # get image data
                width, height = chunk.data["width"], chunk.data["height"]
                img = Image.new("RGBA", (width, height))
                img.frombytes(chunk.data["data"])

                layer_name = layers[chunk.layer_index]
                try:
                    count = frame_count[(anim_name, layer_name)]
                except KeyError:
                    count = 1
                frame_count[(anim_name, layer_name)] = count + 1

                frame_path = os.path.join(scml_dir, scml_name, "%s/%s_%s.%i.png" % (anim_name, anim_name, layer_name, count))
                os.makedirs(os.path.dirname(frame_path), exist_ok=True)
                img.save(frame_path)

                try:
                    anim_layers[anim_name].add(layer_name)
                except KeyError:
                    anim_layers[anim_name] = set([layer_name])

                file = ET.SubElement(folder, "file", id=str(len(folder.findall("./file"))), name=os.path.relpath(frame_path, scml_dir), width=str(width), height=str(height), pivot_x=str(0), pivot_y=str(1))

                frame_file[(frame_index, chunk.layer_index)] = (folder.get("id"), file.get("id"))

    entity = ET.SubElement(spriter_data, "entity", id=str(0), name=scml_name)

    # pass two, extract animations
    interval = 100
    timeline_lookup = {}
    animation = None

    cur_time = 0
    anim_length = 0
    for frame_index,frame in enumerate(parsed_file.frames):
        mainline_key = None
        for chunk in frame.chunks:
            if type(chunk) == aseprite.chunks.CelChunk:
                anim_name = frame_names[frame_index]
                if animation == None or animation.get("name") != anim_name:
                    cur_time = 0
                    if animation != None:
                        animation.set("length", str(anim_length))

                    animation = ET.SubElement(entity, "animation", id=str(len(entity.findall("./animation"))), name=anim_name, interval=str(interval))

                    tmp = list(anim_layers[anim_name])
                    tmp.sort()
                    anim_layers[anim_name] = tmp

                    mainline = ET.SubElement(animation, "mainline")
                    for timeline_id, timeline_layer in enumerate(tmp):
                        timeline = ET.SubElement(animation, "timeline", id=str(timeline_id), name="%s_%s" % (anim_name, timeline_layer))
                        timeline_lookup[timeline_layer] = timeline

                if mainline_key == None:
                    mainline_key = ET.SubElement(mainline, "key", id=str(len(mainline.findall("./key"))), time=str(cur_time), curve_type="instant")

                timeline = timeline_lookup[layers[chunk.layer_index]]
                timeline_key = ET.SubElement(timeline, "key", id=str(len(timeline.findall("./key"))), time=str(cur_time), spin=str(0))
                folder, file = frame_file[(frame_index, chunk.layer_index)]
                _object = ET.SubElement(timeline_key, "object", folder=folder, file=file, x=str(chunk.x_pos + ofs_x), y=str( - chunk.y_pos + ofs_y))
                alpha = layer_alpha[chunk.layer_index]
                if alpha < 255:
                    _object.set("a", str(alpha/255.0))
                index = len(mainline_key.findall("./object_ref"))
                object_ref = ET.SubElement(mainline_key, "object_ref", id=str(index), timeline=timeline.get("id"), key=timeline_key.get("id"), z_index=str(index))

        cur_time += frame.frame_duration
        anim_length = cur_time

    if animation != None:
        animation.set("length", str(anim_length))

    os.makedirs(scml_dir, exist_ok=True)
    with open(scml_path, 'wb') as f:
        tree = ET.ElementTree(spriter_data)
        ET.indent(tree, space="\t")
        tree.write(f, encoding='utf-8', xml_declaration=True)

def main():
    parser = argparse.ArgumentParser(description='Convert a Aseprite animation into a Spriter animation')
    parser.add_argument('input', type=str, help='Input Aseprite animation')
    parser.add_argument('--output', type=str, help='Output scml path')
    parser.add_argument('--ofs_x', type=int, default=0, help="X-offset added to all frames")
    parser.add_argument('--ofs_y', type=int, default=0, help="Y-offset added to all frames")

    args = parser.parse_args()

    in_path = args.input
    out_path = args.output
    if out_path == None:
        out_path = os.path.join("scml", os.path.splitext(os.path.basename(in_path))[0] + ".scml")
    convertAnim(in_path, out_path, args.ofs_x, args.ofs_y)

if __name__ == "__main__":
    # convertAnim(r"RogueAnimations1.5\Rogue.aseprite", "scml/Rogue.scml", -62, 113)
    main()


