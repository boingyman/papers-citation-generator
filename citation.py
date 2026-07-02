# pyright: reportUnusedCallResult=false
import pathlib
from argparse import ArgumentParser
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


def get_preset_text(preset: str) -> tuple[str, str, str]:
    match preset:
        case "placeholder":
            return (
                "<PLACEHOLDER TITLE>",
                "<PLACEHOLDER BODY>",
                "<PLACEHOLDER PENALTY>",
            )
        case "kolechia_no_entry":
            return (
                "M.O.A. CITATION",
                "Protocol violated.\nNo entry from Kolechia",
                "PENALTY ASSESSED - 30 CREDITS",
            )
        case "impor_no_entry":
            return (
                "M.O.A. CITATION",
                "Protocol violated.\nNo entry from Impor",
                "WARNING ISSUED - NO PENALTY",
            )
        case _:
            return ("", "", "")


def draw_insignia(d: ImageDraw.ImageDraw, mask: Image.Image, color: str):
    d.bitmap((150, 88), mask, color)


def draw_line_breaks(d: ImageDraw.ImageDraw, color: str):
    for i in range(0, 83):
        d.rectangle([(16 + i * 4, 34), (17 + i * 4, 35)], color, width=0)
        d.rectangle([(16 + i * 4, 106), (17 + i * 4, 107)], color, width=0)


def draw_edge_perforations(d: ImageDraw.ImageDraw, color: str):
    for i in range(0, 91):
        d.rectangle([(0 + i * 4, 0), (1 + i * 4, 1)], color, width=0)
        d.rectangle([(2 + i * 4, 158), (3 + i * 4, 159)], color, width=0)


def draw_edge(d: ImageDraw.ImageDraw, color: str):
    d.rectangle([(364, 0), (365, 159)], color, width=0)


def draw_holes(d: ImageDraw.ImageDraw, color: str):
    for i in range(0, 9):
        d.rectangle([(4, 6 + i * 18), (9, 11 + i * 18)], color, width=0)
        d.rectangle([(352, 6 + i * 18), (357, 11 + i * 18)], color, width=0)


def draw_barcode(d: ImageDraw.ImageDraw, color: str, barcodeWidth: list[int]):
    xOffset = -2
    barcodeWidth.reverse()
    for w in barcodeWidth:
        xOffset += 2 + (w * 2)
        d.rectangle([(344 - xOffset, 6), (344 - xOffset + (w * 2 - 1), 17)], color)

    d.rectangle([(344 - xOffset - 6, 6), (344 - xOffset - 3, 11)], color)


def get_text_mask(
    header: str, body: str, assessment: str, fontFilePath: str, filter_text: bool = True
):
    textMaskImg = Image.new("L", (366, 160), "#000000")

    textMaskDrawing = ImageDraw.Draw(textMaskImg)
    font = ImageFont.truetype(fontFilePath, 16)

    textMaskDrawing.text(
        (22, 10),
        header,
        font=font,
        fill="#ffffff",
    )

    textMaskDrawing.text(
        (22, 46),
        body,
        font=font,
        fill="#ffffff",
    )

    textMaskDrawing.text(
        (183, 144),
        assessment,
        font=font,
        fill="#ffffff",
        anchor="md",
    )

    if filter_text:
        convFilter = ImageFilter.Kernel(
            (3, 3), [0.01, 0.15, 0.01, 0.07, 0.0, 0.07, 0.0, 0.1, 0.0]
        )

        horizMaskFilter = ImageFilter.Kernel(
            (5, 5),
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        )

        filterRes = ImageChops.multiply(
            textMaskImg.filter(convFilter), Image.new("L", (366, 160), "#828282")
        )

        horizMaskRes = (
            textMaskImg.filter(horizMaskFilter)
            .filter(horizMaskFilter)
            .filter(horizMaskFilter)
        )

        # interesting thing pointed out by pyright
        # appears to be a special case of get_flattened_data where it returns a tuple[int, ...] instead of tuple[tuple[int, ...], ...]?
        horizMaskData: tuple[int, ...] = horizMaskRes.get_flattened_data(0)  # pyright: ignore[reportAssignmentType]
        thresholdRes: list[int] = [255 if p > 0 else 0 for p in horizMaskData]
        # putdata also doesn't list tuple[int, ...] as part of the parameter type hint?
        horizMaskRes.putdata(thresholdRes)  # pyright: ignore[reportUnknownMemberType]

        filterRes = ImageChops.multiply(filterRes, horizMaskRes)

        textMaskImg = ImageChops.add(textMaskImg, filterRes)

    return textMaskImg


def parse_arg_as_color_code(arg: str | None) -> str | None:
    if arg is None:
        return None

    if len(arg) > 1 and len(arg) <= 9 and arg[0] == "#":
        arg = arg.lower()
        for c in arg[1:-1]:
            if c not in "0123456789abcdef":
                raise Exception("Color argument was not in hexadecimal format.")

        if len(arg[1:]) == 2:
            return "#" + arg[1:] + arg[1:] + arg[1:] + "ff"

        if len(arg[1:]) == 6:
            return "#" + arg[1:] + "ff"

        if len(arg[1:]) == 8:
            return arg

    raise Exception("Color argument was not in the correct format.")


def generate_color_palette(paper_color: str) -> tuple[str, str, str]:
    if len(paper_color) != 9:
        raise Exception("Base color input is not in the correct format.")

    for c in paper_color[1:]:
        if c not in "0123456789abcdef":
            raise Exception("Base color input was not in hexadecimal format.")

    r, g, b = (paper_color[1:3], paper_color[3:5], paper_color[5:7])

    def _multiply_color_value(_l: str, _r: float) -> str:
        return ("0" + (hex(round((int(_l, 16) / 255 * _r) * 255))[2:]))[-2:]

    ink = (
        "#"
        + _multiply_color_value(r, 0.37037037037037035)
        + _multiply_color_value(g, 0.3953488372093023)
        + _multiply_color_value(b, 0.3869565217391304)
        + "ff"
    )
    tertiary = (
        "#"
        + _multiply_color_value(r, 0.7860082304526749)
        + _multiply_color_value(g, 0.7813953488372093)
        + _multiply_color_value(b, 0.7304347826086957)
        + "ff"
    )

    return ink, paper_color, tertiary


def save_animated_file(base_image: Image.Image, output_path: str) -> None:
    frames: list[Image.Image] = list()

    y_offset = -2
    launch_multiplier = 3.0

    for i in range(0, 140):
        frm = Image.new("RGBA", (366, 222), "#00000000")
        # ~ 2 pixels per frame
        if i < 20:
            y_offset += 2
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)
        elif i < 40:
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)
        elif i < 60:
            y_offset += 2
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)
        elif i < 80:
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)
            pass
        elif i < 100:
            y_offset += 2
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)
        elif i < 120:
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)
        else:
            y_offset += round(7 * launch_multiplier)
            launch_multiplier = launch_multiplier * 0.8
            frm.paste(base_image, (0, 222 - y_offset))
            frames.append(frm)

    for i in range(0, 150):
        frames.append(frames[-1].copy())

    final = Image.new("RGBA", (366, 222), "#00000000")

    final.save(
        output_path,
        save_all=True,
        append_images=frames,
        duration=20,
        loop=0,
        disposal=2,
    )


def main():
    parser = ArgumentParser(
        description="Generates a custom citation from Papers, Please."
    )

    parser.add_argument(
        "-im",
        "--insignia-mask",
        dest="insignia_path",
        type=str,
        default=pathlib.Path(".", "pp_citation_emblem.bmp"),
        help="Path to a black and white, 64x64 image used for the watermark.",
    )

    parser.add_argument(
        "-ic",
        "--ink-color",
        dest="ink_color",
        type=parse_arg_as_color_code,
        default=None,
        help="Color for the elements of the citation that are made of ink.",
    )

    parser.add_argument(
        "-pc",
        "--paper-color",
        dest="paper_color",
        type=parse_arg_as_color_code,
        default=None,
        help="Color of the citation's paper.",
    )

    parser.add_argument(
        "-tc",
        "--tertiary-color",
        dest="tertiary_color",
        type=parse_arg_as_color_code,
        default=None,
        help="Color of decorative elements of the citation, such as the perforation marks and watermark.",
    )

    parser.add_argument(
        "-ba",
        "--barcode",
        dest="barcode",
        type=lambda x: [int(i) for i in x.split(",")],
        default="1,1,1,2,2",
        help="A comma separated (without spaces) list of values greater than 1 to generate the citation's barcode.",
    )

    parser.add_argument(
        "-ht",
        "--header-text",
        dest="header_text",
        type=str,
        default=None,
        help="The text of the header.",
    )

    parser.add_argument(
        "-bt",
        "--body-text",
        dest="body_text",
        type=str,
        default=None,
        help="The text of the body.",
    )

    parser.add_argument(
        "-pt",
        "--penalty-text",
        dest="penalty_text",
        type=str,
        default=None,
        help="The text of the penalty. (Center aligned)",
    )

    parser.add_argument(
        "-pr",
        "--preset",
        dest="preset_text",
        type=str,
        default="kolechia_no_entry",
        help="Existing presets to utilize for the text. Has lower priority.",
    )

    parser.add_argument(
        "-ap",
        "--auto-penalty",
        dest="auto_penalty",
        type=lambda x: (
            "PENALTY ASSESSED - " + str((int(x) - 2) * 5) + " CREDITS"
            if int(x) > 4
            else [
                "WARNING ISSUED - NO PENALTY",
                "LAST WARNING - NO PENALTY",
                "PENALTY ASSESSED - 5 CREDITS",
                "PENALTY ASSESSED - 5 CREDITS",
            ][int(x) - 1]
        ),
        default=None,
        help="An integer value used to determine penalty text. Follows the same format as the game: 1 = Warning, 2 = Last Warning, 3/4 = 5 Credits, 5+ = (X - 2) * 5 Credits",
    )

    parser.add_argument(
        "-an",
        "--animated",
        dest="animated",
        action="store_true",
        help="Make the resulting image animated as if it was being printed.",
    )

    parser.add_argument(
        "-pl",
        "--palette-color",
        dest="palette_color",
        type=parse_arg_as_color_code,
        default="#f3d7e6ff",
        help="Generate a color palette. Has lower priority.",
    )

    parser.add_argument(
        "-df",
        "--disable-text-filter",
        dest="disable_text_filter",
        action="store_true",
        help="Disables the filter applied to text.",
    )

    parser.add_argument(
        "-avif",
        "--output-avif",
        dest="avif",
        action="store_true",
        help="The resulting file will be in the AVIF format.",
    )

    parser.add_argument(
        "-o",
        "--output-path",
        dest="output_path",
        type=str,
        default=pathlib.Path(".", "citation.png"),
        help="The output path of the file. The appropriate file extension will be modified for the correct output.",
    )

    parser.add_argument(
        "-fo",
        "--font",
        dest="font_path",
        type=str,
        default=pathlib.Path(".", "BMmini.ttf"),
        help="The path to the font file that will be used to render text.",
    )

    @dataclass
    class CitationArgs:
        insignia_path: str
        ink_color: str | None
        paper_color: str | None
        tertiary_color: str | None
        barcode: list[int]
        header_text: str | None
        body_text: str | None
        penalty_text: str | None
        preset_text: str
        auto_penalty: str | None
        animated: bool
        palette_color: str
        disable_text_filter: bool
        avif: bool
        output_path: str
        font_path: str

    result_args = CitationArgs(**vars(parser.parse_args()))  # pyright:ignore[reportAny]

    # make it so the manual arguments take highest priority
    header_text, body_text, penalty_text = get_preset_text(result_args.preset_text)

    if result_args.auto_penalty is not None:
        penalty_text = result_args.auto_penalty

    if result_args.header_text is not None:
        header_text = result_args.header_text
    if result_args.body_text is not None:
        body_text = result_args.body_text
    if result_args.penalty_text is not None:
        penalty_text = result_args.penalty_text

    ink_color, paper_color, tertiary_color = generate_color_palette(
        result_args.palette_color
    )

    if result_args.ink_color is not None:
        ink_color = result_args.ink_color
    if result_args.paper_color is not None:
        paper_color = result_args.paper_color
    if result_args.tertiary_color is not None:
        tertiary_color = result_args.tertiary_color

    output_path = result_args.output_path

    if result_args.avif:
        output_path = str(pathlib.Path(output_path).with_suffix(".avif"))
    elif result_args.animated:
        output_path = str(pathlib.Path(output_path).with_suffix(".gif"))
    else:
        output_path = str(pathlib.Path(output_path).with_suffix(".png"))

    img = Image.new("RGBA", (366, 160), paper_color)

    drawing = ImageDraw.Draw(img)

    draw_insignia(
        drawing,
        Image.open(result_args.insignia_path).convert("L"),
        tertiary_color,
    )
    draw_edge_perforations(drawing, tertiary_color)
    draw_edge(drawing, tertiary_color)
    draw_holes(drawing, tertiary_color)
    draw_line_breaks(drawing, ink_color)
    draw_barcode(drawing, ink_color, result_args.barcode)

    textMask = get_text_mask(
        header_text,
        body_text,
        penalty_text,
        result_args.font_path,
        not result_args.disable_text_filter,
    )

    img = Image.composite(Image.new("RGBA", (366, 160), ink_color), img, textMask)

    if result_args.animated:
        save_animated_file(
            img,
            output_path,
        )
    else:
        img.save(output_path)


if __name__ == "__main__":
    main()
