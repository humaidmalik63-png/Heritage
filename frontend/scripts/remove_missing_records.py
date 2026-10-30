import json

home = r"C:\Users\humai\AI"
cat_path = r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json"
output_path = cat_path

# The site_ids to remove
remove_ids = {
    "former_populated_place_in_agarak_aragatsotn_armenia",
    "ghafuri_house_mashhad_iran",
    "musel_island",
    "palace_hotel_broken_hill_australia",
    "statue_liberty",
    "vernacular_architecture_in_butuceni_orhei_moldova",
    "category_angkor_thom_cambodia",
    "category_almaty_opera_ballet_theatre_kazakhstan",
    "house_of_secundus_tyrannus_fortunatus_italy",
}

# Load the catalogue
with open(cat_path, encoding="utf-8") as f:
    catalogue = json.load(f)

# Filter out the entries with the site_ids to remove
filtered = [rec for rec in catalogue if rec.get("site_id") not in remove_ids]

print(f"Original count: {len(catalogue)}")
print(f"Filtered count: {len(filtered)}")
print("Removed IDs:", sorted(remove_ids))

# Write back to the same file (backup first)
backup_path = cat_path + ".backup"
import shutil
shutil.copy2(cat_path, backup_path)
print(f"Backup written to {backup_path}")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Updated catalogue written to {output_path}")