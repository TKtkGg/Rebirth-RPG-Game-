import { PlayerScreenData } from "../types/player_types";
import { InventoryItemData, ItemScreenData } from "../types/item_types";

export type InventoryScreenData = {
    "player": PlayerScreenData;
    "inventory_items": InventoryItemData[];
    "selected_item": {
        "id": number;
        "item": ItemScreenData;
        "quantity": number;
    } | null;
    "category": string;
    "search_query": string | null;
    "use_message": string | null;
}