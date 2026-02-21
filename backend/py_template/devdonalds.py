import string

from dataclasses import dataclass
from typing import List, Literal, TypedDict
from flask import Flask, request, jsonify

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int

@dataclass
class RecipeEntry(CookbookEntry):
	type: Literal["recipe"]
	name: str
	requiredItems: list[RequiredItem]

@dataclass
class IngredientEntry(CookbookEntry):
	type: Literal["ingredient"]
	name: str
	cookTime: int

class ReturnIngredient(TypedDict):
	name: str
	quantity: int

class RecursiveState(TypedDict):
	name: str
	cookTime: int
	ingredients: dict[str, int]

# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: dict[str, IngredientEntry | RecipeEntry] = {}

# Endpoint to clear the cookbook
@app.route("/clear", methods=['POST'])
def clear():
	global cookbook
	cookbook = {}
	return jsonify({}), 200

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> str | None:
	buff = []
	valid_chars = string.ascii_letters + " "
	for c in recipeName:
		if c in "_- ":
			if not buff or buff[-1] == " ":
				continue
			buff.append(" ")
		elif c not in valid_chars:
			continue
		elif not buff or buff[-1] == " ":
			buff.append(c.upper())

		elif buff[-1] != " ":
			buff.append(c.lower())

	if not len(buff):
		return None
	return "".join(buff).strip()


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	status = handle_create_recipe(data)

	if not status:
		return {"error": "Failed to save entry."}, 400
	return jsonify({}), 200


def handle_create_recipe(entry: dict) -> bool:
	if cookbook.get(entry["name"]):
		return False
	model = None
	if entry["type"] == "recipe":
		entry["requiredItems"] = [RequiredItem(**i) for i in entry.get("requiredItems", [])]
		model = RecipeEntry(**entry)
		# We can also do set_ = set([item.name for item in model.requiredItems])
		# and compare the length, but this is also a solution.
		set_ = set()
		# O(n) time complexity since item lookup in set is O(1)
		for item in model.requiredItems:
			if item.name in set_:
				return False 
			set_.update({item.name})

	elif entry["type"] == "ingredient":
		model = IngredientEntry(**entry)
		if model.cookTime < 0:
			return False
	else:
		return False

	cookbook[entry["name"]] = model
	return True

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args["name"]
	state = handle_get_recipe(name, {"name": name, "cookTime": 0, "ingredients": {}})

	if not state:
		return {"error": "Failed to load recipe."}, 400

	return jsonify({
		"name": state["name"],
		"cookTime": state["cookTime"],
		"ingredients": [{"name": k, "quantity": v} for k, v in state["ingredients"].items()]
	}), 200

def handle_get_recipe(name: str, state: RecursiveState, quantity: int = 1) -> RecursiveState | None:
	entry = cookbook.get(name)
	if not entry:
		return None
	if entry.type == "ingredient":
		# This is the searched recipe
		if entry.name == state["name"]:
			return None
		state["cookTime"] += entry.cookTime * quantity
		state["ingredients"][name] = state["ingredients"].get(name, 0) + quantity
		return state
	for ingr in entry.requiredItems:
		recipe = handle_get_recipe(name=ingr.name, state=state, quantity=quantity * ingr.quantity)
		# Fail everything if any recipe is not in the cookbook.
		if recipe is None:
			return None
	return state



# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
