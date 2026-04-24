import { PlayerScreenData } from "../types/player_types";
import { EquipmentScreenData } from "../types/equipment_types";
import { ItemScreenData } from "../types/item_types";

export type ShopScreenData = {
    "player": PlayerScreenData;
    "weapons": EquipmentScreenData[];
    "armors": EquipmentScreenData[];
    "items": ItemScreenData[];
    "session_purchased": string;
}

export type ShopDisplayItem =
    | ({ type: "weapon" | "armor"; iconPath: string } & EquipmentScreenData)
    | ({ type: "item"; iconPath: string } & ItemScreenData);