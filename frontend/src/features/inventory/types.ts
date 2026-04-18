import { PlayerScreenData } from "../types/player_types";
import { ItemScreenData } from "../types/item_types";

export type InventoryScreenData = {
    "player": PlayerScreenData;
    "inventory_items": {
        "id": number;
        "item": ItemScreenData;
        "quantity": number;
    }[];
    "selected_item": {
        "id": number;
        "item": ItemScreenData;
        "quantity": number;
    } | null;
    "category": string;
    "search_query": string | null;
    "use_message": string | null;
}