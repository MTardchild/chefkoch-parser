from bs4 import BeautifulSoup, Tag
from pylatex import Document, Section, LongTabu, LargeText, VerticalSpace, Figure, Center, Command, MiniPage, LineBreak
from pylatex.utils import bold
from urllib.request import urlopen
from pathlib import Path


def get_ingredients(parsed):
    ingredients_table = parsed.find(class_="incredients")
    ingredients_amount = []
    ingredients_name = []
    for ingredient_row in ingredients_table:
        if isinstance(ingredient_row, Tag):
            columns = ingredient_row.find_all('td')
            for j, column in enumerate(columns):
                parsed_string = ""
                if column.a:
                    parsed_string = column.a.string.strip().replace("\xa0", " ")
                else:
                    if column.sup:
                        strings = column.get_text()
                        for s in strings:
                            if s.isalpha():
                                parsed_string += " "
                                parsed_string += s
                            else:
                                parsed_string += s
                    else:
                        parsed_string = column.get_text().strip().replace("\xa0", " ")
                if j % 2 == 1:
                    ingredients_name.append(parsed_string)
                else:
                    ingredients_amount.append(parsed_string)
    return ingredients_amount, ingredients_name


def get_instructions(parsed):
    instructions_html = parsed.find(id="rezept-zubereitung").strings
    instruction_string = ""
    for instructionHtml in instructions_html:
        instruction_string += instructionHtml
    instructions_split = instruction_string.split(chr(10))
    instructions = [x.lstrip() for x in instructions_split if not is_whitespace(x)]
    return instructions


def is_whitespace(str):
    return len(str) == 0 or str.isspace()


def generate_tex(i, recipe_title, ingredients_amount, ingredients_name, instructions):
    geometry_options = {
        "head": "30pt",
        "margin": "0.6in",
        "bottom": "0.8in",
    }
    doc = Document(geometry_options=geometry_options)
    doc.change_length("\parindent", "0pt")
    doc.add_color("strongRed", "HTML", "f44242")
    doc.add_color("lightRed", "HTML", "ffc1c1")
    with doc.create(Center()):
        doc.append(LargeText(bold(recipe_title)))
    doc.append(VerticalSpace("0pt"))
    doc.append(Command('small'))
    with doc.create(LongTabu("X[l] X[3l]", row_height=1.5)) as ingredientTable:
        ingredientTable.add_row(["Menge", "Zutat"], mapper=bold, color="strongRed")
        ingredientTable.add_hline()
        for j, ingredientAmount in enumerate(ingredients_amount):
            row = [bold(ingredientAmount), bold(ingredients_name[j])]
            if (j % 2) == 0:
                ingredientTable.add_row(row, color="lightRed")
            else:
                ingredientTable.add_row(row)
    doc.append(VerticalSpace("0pt"))
    doc.append(Command('large'))
    with doc.create(Section("Anweisungen", False)):
        for instruction in instructions:
            doc.append(instruction)
    with doc.create(Figure(position="h")) as pic:
        pic.add_image("picture" + str(i) + ".jpg", width="220px")
    path = "recipes/" + recipe_title.replace(" ", "")
    print("Created:" + path + ".tex")
    try:
        doc.generate_tex(path)
    except Exception:
        pass


def generate_html(i, recipe_title, ingredients_amount, ingredients_name, instructions):
    contents = Path("template.html").read_text()
    parsed = BeautifulSoup(contents, 'html.parser')
    instructions_div = parsed.select("#instructions")[0]
    table_body = parsed.select("#ingredients_body")[0]
    parsed.select("#title")[0].append(recipe_title)
    parsed.select("#image")[0].append(BeautifulSoup("<img width=\"100%\" src=\"picture" + str(i) + ".jpg\">", "html.parser"))
    for j, ingredient_amount in enumerate(ingredients_amount):
        table_body.append(BeautifulSoup("<tr><td>" + ingredient_amount
                                        + "</td><td>" + ingredients_name[j] + "</td></tr>", "html.parser"))
    for instruction in instructions:
        instructions_div.append(BeautifulSoup("<p>" + instruction + "</p>", "html.parser"))

    file = open("recipes/" + recipe_title + ".html", "w")
    file.write(parsed.prettify())


def little_do_it_all():
    with open("urls.txt") as f:
        urls = f.readlines()
    urls = [url.strip() for url in urls]

    for i, url in enumerate(urls):
        page = urlopen(url)
        parsed = BeautifulSoup(page, 'html.parser')
        ingredients_amount, ingredients_name = get_ingredients(parsed)
        instructions = get_instructions(parsed)
        recipe_title = parsed.find(class_="page-title").string
        picture_url = parsed.find(class_="slideshow-image").attrs['src']
        picture_response = urlopen(picture_url)
        picture = picture_response.read()
        try:
            with open("recipes/picture" + str(i) + ".jpg", "wb+") as f:
                f.write(picture)
        except OSError:
            print("Error trying to write picture to filesystem.")
        generate_tex(i, recipe_title, ingredients_amount, ingredients_name, instructions)
        generate_html(i, recipe_title, ingredients_amount, ingredients_name, instructions)


little_do_it_all()
