from html.parser import HTMLParser


class IngredientParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.capture_depth = 0
        self.ingredients = []
        self.current_ingredient = ""
        self.capture_title = False
        self.title = ""
        self.description = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # Increment capture depth if we're either already capturing, or we find a "text-ingredient" class
        if self.capture_depth > 0 or ("class" in attrs and attrs["class"] and "text-ingredient" in attrs["class"]):
            self.capture_depth += 1
        if tag == "title":
            self.capture_title = True
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content")

    def handle_endtag(self, tag):
        if self.capture_depth > 0:
            self.capture_depth -= 1
            # Only capture the ingredient once we're leaving the outermost tag of interest
            if self.capture_depth == 0:
                self.ingredients.append(self.current_ingredient.strip())
                self.current_ingredient = ""
        self.capture_title = False

    def handle_data(self, data):
        if self.capture_depth > 0:
            self.current_ingredient += data
        elif self.capture_title:
            self.title = data.replace(" - LeukeRecepten", "")

    def get_ingredients(self):
        return [ingredient for ingredient in self.ingredients if ingredient[0].isnumeric()]
