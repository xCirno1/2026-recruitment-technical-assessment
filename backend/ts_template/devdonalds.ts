import express from "express";
import type { Request, Response } from "express";

// ==== Type Definitions, feel free to add or modify ==========================
interface cookbookEntry {
  name: string;
  type: string;
}

interface requiredItem {
  name: string;
  quantity: number;
}

interface recipe extends cookbookEntry {
  type: "recipe";
  requiredItems: requiredItem[];
}

interface ingredient extends cookbookEntry {
  type: "ingredient";
  cookTime: number;
}

interface RecursiveState {
  name: string;
  cookTime: number;
  ingredients: Map<string, number>
}

// =============================================================================
// ==== HTTP Endpoint Stubs ====================================================
// =============================================================================
const app = express();
app.use(express.json());

let cookbook: Map<string, Map<any, any>> = new Map();

app.post("/clear", (req: Request, res: Response) => {
  cookbook = new Map();
  return res.json({});
});

// Task 1 helper (don't touch)
app.post("/parse", (req: Request, res: Response) => {
  const { input } = req.body;

  const parsed_string = parse_handwriting(input)
  if (parsed_string == null) {
    res.status(400).send("this string is cooked");
    return;
  }
  res.json({ msg: parsed_string });
  return;

});

// [TASK 1] ====================================================================
// Takes in a recipeName and returns it in a form that 
const parse_handwriting = (recipeName: string): string | null => {
  let buff = [];
  recipeName = recipeName.replace(/[^a-z_\- ]/gi, "");
  for (const c of recipeName) {
    if ("_- ".includes(c)) {
      if (!buff.length || buff[buff.length - 1] == " ") {
        continue
      }
      buff.push(" ");
    } else if (!buff.length || buff[buff.length - 1] == " ") {
      buff.push(c.toUpperCase());
    } else if (buff[buff.length - 1] != " ") {
      buff.push(c.toLowerCase());
    }
  }
  if (!buff.length) {
    return null;
  }
  return buff.join("").trim();
}

// [TASK 2] ====================================================================
// Endpoint that adds a CookbookEntry to your magical cookbook
app.post("/entry", (req: Request, res: Response) => {
  const status = handle_create_recipe(req.body);
  if (!status) {
    return res.status(400).json({ error: "Failed to save entry." })
  }
  return res.json({})
});

const handle_create_recipe = (entry: recipe | ingredient): boolean => {
  if (cookbook[entry.name]) {
    return false;
  }
  if (entry.type == "recipe") {
    let set_ = new Set(
      (entry as recipe).requiredItems.map(v => v.name)
    );
    if (set_.size !== entry.requiredItems.length) {
      return false;
    }
  } else if (entry.type == "ingredient") {
    if (entry.cookTime < 0) {
      return false;
    }
  } else {
    return false;
  }
  cookbook[entry.name] = entry;
  return true;
}

// [TASK 3] ====================================================================
// Endpoint that returns a summary of a recipe that corresponds to a query name
app.get("/summary", (req: Request, res: Response) => {
  const name = req.query.name as string;
  const state: RecursiveState = handle_get_recipe(name, { name, cookTime: 0, ingredients: new Map() });

  if (!state) {
    return res.status(400).json({ error: "Failed to load recipe." })
  }
  return res.json({
    name: state.name,
    cookTime: state.cookTime,
    // .map's parameter is array [key, value]
    ingredients: Object.entries(state.ingredients).map((t) => {
      return { name: t[0], quantity: t[1] }
    })
  })
});

const handle_get_recipe = (name: string, state: RecursiveState, quantity: number = 1) => {
  const entry: ingredient | recipe = cookbook[name];
  if (!entry) {
    return null;
  }
  if (entry.type === "ingredient") {
    if (entry.name == state.name) {
      return null;
    }
    state.cookTime += entry.cookTime * quantity;
    state.ingredients[name] = (state.ingredients[name] ?? 0) + quantity;
    return state;
  }
  for (const ingr of entry.requiredItems) {
    let recipe = handle_get_recipe(ingr.name, state, quantity * ingr.quantity);
    if (!recipe) {
      return null;
    }
  }
  return state;
}

// =============================================================================
// ==== DO NOT TOUCH ===========================================================
// =============================================================================
const port = 8080;
app.listen(port, () => {
  console.log(`Running on: http://127.0.0.1:8080`);
});
