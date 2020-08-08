#!/usr/bin/env python

import json
import os

import gimpenums
from gimpfu import *


# Taken from https://github.com/jarnik/gimp-export-spritesheet/blob/master/pygimplib/pgpdb.py#L112
def duplicate_metadata(image):
    new_image = pdb.gimp_image_new(image.width, image.height, image.base_type)
    pdb.gimp_image_set_resolution(new_image, *pdb.gimp_image_get_resolution(image))

    if image.base_type == gimpenums.INDEXED:
        pdb.gimp_image_set_colormap(new_image, *pdb.gimp_image_get_colormap(image))
    _, parasite_names = pdb.gimp_image_get_parasite_list(image)
    for name in parasite_names:
        parasite = image.parasite_find(name)
        new_image.parasite_attach(
            gimp.Parasite(parasite.name, parasite.flags, parasite.data)
        )

    return new_image


def export_spritesheet(image, layer, output_folder):
    spritesheet_name = os.path.splitext(image.name)[0]
    img_filename = "%s.png" % (spritesheet_name)
    output_path = output_folder + os.sep + img_filename
    json_path = output_folder + os.sep + "%s.json" % (spritesheet_name)

    spritesheet = duplicate_metadata(image)
    sprites = 0
    if len(image.layers) > 0:
        frame_width = image.layers[0].width
        frame_height = image.layers[0].height
    else:
        frame_width = 0
        frame_height = 0
    if any(
        l.visible and (l.width != frame_width or l.height != frame_height)
        for l in image.layers
    ):
        raise Exception("All layers must have the same dimensions")
    for i in reversed(range(len(image.layers))):
        if not image.layers[i].visible:
            continue
        layer_copy = pdb.gimp_layer_new_from_drawable(image.layers[i], spritesheet)
        pdb.gimp_image_insert_layer(spritesheet, layer_copy, None, sprites)
        pdb.gimp_item_set_visible(layer_copy, True)
        pdb.gimp_layer_set_offsets(
            spritesheet.layers[sprites], (len(image.layers) - 1 - i) * frame_width, 0
        )
        sprites += 1

    pdb.gimp_image_resize(spritesheet, frame_width * sprites, frame_height, 0, 0)
    layer = pdb.gimp_image_merge_visible_layers(spritesheet, gimpenums.CLIP_TO_IMAGE)
    pdb.file_png_save(
        spritesheet,
        spritesheet.layers[0],
        output_path,
        output_path,
        0,
        9,
        0,
        0,
        0,
        0,
        0,
    )
    pdb.gimp_image_delete(spritesheet)

    obj = {
        "frames": sprites,
        "frame_width": frame_width,
        "frame_height": frame_height,
    }
    with open(json_path, "w") as f:
        json.dump(obj, f, sort_keys=True, separators=(", ", ": "), indent=4)


register(
    "python_fu_export_spritesheet",
    "Export spritesheet",
    "Export spritesheet.",
    "Rodrigo Gryzinski",
    "MIT",
    "2020",
    "<Image>/File/Export/Export Spritesheet",
    "*",
    [(PF_DIRNAME, "output_folder", "Output directory", os.path.expanduser("~")),],
    [],
    export_spritesheet,
)

main()
