import os
import cv2
from xml.etree import ElementTree
import json


def main(image_dir, xml_dir, output_dir):
    output_image = os.path.join(output_dir, image_dir)
    try:
        os.makedirs(output_image)
    except FileExistsError:
        pass

    resize_images(image_dir, output_image)

    resize_bboxes(xml_dir, output_dir)


def resize_bboxes(directory, output):
    category_names = set()
    categories = []
    images = []
    annotations = []

    id_cat = 0
    id_im = 0
    id_ann = 0

    for file in os.listdir(directory):
        xml_root = ElementTree.parse(os.path.join(directory, file)).getroot()

        file_name, width, height, category_name, xmin, ymin, xmax, ymax = parse_xml(xml_root)

        if category_name not in category_names:
            category_names.add(category_name)
            categories.append({
                "id": id_cat,
                "name": category_name,
                "supercategory": "none"
            })
            id_cat += 1

        category_index = None
        for i, category in enumerate(categories):
            if category["name"] == category_name:
                category_index = i
                break

        if width > 800:
            xmin = round((xmin * 800) / width)
            xmax = round((xmax * 800) / width)
            width = 800

        if height > 450:
            ymin = round((ymin * 450) / height)
            ymax = round((ymax * 450) / height)
            height = 450

        images.append({
            "id": id_im,
            "width": width,
            "height": height,
            "file_name": file_name
        })

        annotations.append({
            "id": id_ann,
            "image_id": id_im,
            "category_id": categories[category_index]["id"],
            "bbox": [xmin, ymin, xmax - xmin, ymax - ymin]
        })
        id_im += 1

    json_data = {
        "categories": categories,
        "images": images,
        "annotations": annotations
    }

    with open(os.path.join(output, "data.json"), "w") as f:
        json.dump(json_data, f)


def parse_xml(root):
    file_name = width = height = category_name = xmin = ymin = xmax = ymax = None

    for child in root:
        match child.tag:
            case "filename":
                file_name = child.text
            case "size":
                for dim in child:
                    match dim.tag:
                        case "width":
                            width = int(dim.text)
                        case "height":
                            height = int(dim.text)
            case "object":
                for spec in child:
                    match spec.tag:
                        case "name":
                            category_name = spec.text
                        case "bndbox":
                            for coor in spec:
                                match coor.tag:
                                    case "xmin":
                                        xmin = int(coor.text)
                                    case "ymin":
                                        ymin = int(coor.text)
                                    case "xmax":
                                        xmax = int(coor.text)
                                    case "ymax":
                                        ymax = int(coor.text)

    return file_name, width, height, category_name, xmin, ymin, xmax, ymax


def resize_images(directory, output):
    for file in os.listdir(directory):
        image = cv2.imread(os.path.join(directory, file))

        h, w, d = image.shape
        if h > 450 and w > 800:
            image = cv2.resize(image, (800, 450))
        elif h > 450:
            image = cv2.resize(image, (w, 450))
        elif w > 800:
            image = cv2.resize(image, (800, h))
        cv2.imwrite(os.path.join(output, file), image)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--imagedir", help="Image directory")
    parser.add_argument("--xmldir", help="XML directory")
    parser.add_argument("--outputdir", help="Output directory")

    args = vars(parser.parse_args())

    imagedir = args["imagedir"]
    xmldir = args["xmldir"]
    outputdir = args["outputdir"]

    main(imagedir, xmldir, outputdir)
