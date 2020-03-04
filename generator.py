import argparse
import csv
import svgwrite
import base64
import os


class Attendee:
    ROLE_COLORS = {"Organisateur": svgwrite.rgb(255, 0, 0),
                   "Orateur": svgwrite.rgb(0, 150, 0)}
    ROLE_COLOR_DEFAULT = svgwrite.rgb(255, 255, 255)

    def __init__(self, last, first, inst, role, diet):
        self.last = last.upper()
        self.first = first.title()
        self.inst = inst.title()
        self.file_name = "{}_{}_badge.svg".format(self.last, self.first)
        self.role = role
        self.color = Attendee.ROLE_COLORS.get(self.role, Attendee.ROLE_COLOR_DEFAULT)
        self.diet = diet.upper()


def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("attendees_csv")
    parser.add_argument("meals_csv")
    parser.add_argument("--csv-fields", "-f", type=int, nargs=5, default=[0, 1, 2, 3, 4])
    parser.add_argument("--badge-width", "-w", type=int, default=90)
    parser.add_argument("--badge-height", "-h", type=int, default=55)
    parser.add_argument("--logo")
    parser.add_argument("--output-dir", "-o", default="out")
    return parser.parse_args()


def parse_attendees(file_path, fields):
    with open(file_path) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.reader(f, dialect)
        return [Attendee(*(row[j] for j in fields)) for row in reader]


def parse_meals(file_path):
    with open(file_path) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.reader(f, dialect)
        return list(reader)


def create_svg_template(width, height, meals, logo):
    svg = svgwrite.Drawing("template.svg", ("{}mm".format(2*width), "{}mm".format(height)), profile="full")
    w, h = 200*width, 100*height
    svg.viewbox(0, 0, w, h)
    svg.add(svg.rect((0, 0), (w, h), stroke=svgwrite.rgb(0, 0, 0), stroke_width=10, fill=svgwrite.rgb(255, 255, 255)))

    name_txt = svg.add(svg.text("", text_anchor="middle", font_size=640))
    first_txt = name_txt.add(svg.tspan("", x=(0,), y=(0,)))
    last_txt = name_txt.add(svg.tspan("", x=(0,), y=(680,)))
    name_txt.translate(0.81 * w, 0.4 * h)

    inst_txt = svg.add(svg.text("", (0.81 * w, 0.75 * h), text_anchor="middle", font_size=480))

    role_poly_group = svg.add(svg.g())
    role_poly_group.add(svg.polygon([(0.99 * w, 0.99 * h), (0.58 * w, 0.99 * h),
                                     (0.66 * w, 0.82 * h), (0.96 * w, 0.82 * h)]))
    role_poly_group.add(svg.polygon([(0.99 * w, 0.01 * h), (0.58 * w, 0.01 * h),
                                     (0.66 * w, 0.2 * h), (0.96 * w, 0.2 * h)]))

    if logo is not None:
        with open(logo, 'rb') as f:
            logo_b64 = base64.b64encode(f.read()).decode("ascii")
        logo_size = min(0.2 * w, 0.33 * h)
        img = svg.defs.add(svg.image("data:image/png;base64,{}".format(logo_b64),
                                     size=(logo_size, logo_size), id="logo"))
        img.translate(-0.5 * logo_size, -0.5 * logo_size)
        svg.add(svg.use(img, (0.58 * w, 0.5 * h)))

    diet_txt = svg.defs.add(svg.text("", text_anchor="middle", font_size=480, id="diet",
                                     opacity=0.4, fill=svgwrite.rgb(0, 150, 0)))

    n = len(meals)
    for i, (day, date, hour, label, sub_label) in enumerate(meals, start=1):
        svg.add(svg.line((0.5 * w * i / n, 0.05 * h), (0.5 * w * i / n, 0.95 * h), stroke=svgwrite.rgb(0, 0, 0),
                         stroke_width=10, stroke_dasharray="{:.0f}".format(0.06 * h)))

        u = svg.add(svg.use(diet_txt))
        u.translate((0.5 * w * (i - 0.45) / n, 0.5 * h))
        u.rotate(-75)

        svg.add(svg.text(day, (0.5 * w * (i - 0.5) / n, 0.1 * h), text_anchor="middle", font_size=320))
        svg.add(svg.text(date, (0.5 * w * (i - 0.5) / n, 0.17 * h), text_anchor="middle", font_size=280))
        svg.add(svg.text(hour, (0.5 * w * (i - 0.5) / n, 0.24 * h), text_anchor="middle", font_size=280))

        txt = svg.add(svg.text("", text_anchor="middle", font_size=280))
        txt.add(svg.tspan(label, x=(0,), y=(0,)))
        txt.add(svg.tspan(sub_label, x=(0,), y=(320,)))
        txt.translate((0.5 * w * (i - 0.5) / n, 0.5 * h))
        txt.rotate(-90)

        if logo is not None:
            u = svg.add(svg.use(img))
            u.translate((0.5 * w * (i - 0.5) / n, 0.87 * h))
            u.scale(0.6)

    return svg, first_txt, last_txt, inst_txt, role_poly_group, diet_txt


def main(args):
    attendees = parse_attendees(args.attendees_csv, args.csv_fields)
    meals = parse_meals(args.meals_csv)
    svg, first_txt, last_txt, inst_txt, role_poly_group, diet_txt = create_svg_template(
        args.badge_width, args.badge_height, meals, args.logo)
    os.makedirs(args.output_dir, exist_ok=True)

    for attendee in attendees:
        last_txt.text = attendee.last
        first_txt.text = attendee.first
        inst_txt.text = attendee.inst
        role_poly_group.fill(attendee.color)
        diet_txt.text = attendee.diet
        svg.saveas(os.path.join(args.output_dir, attendee.file_name), True)


if __name__ == "__main__":
    main(parse_args())
