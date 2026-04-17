import { PlayerScreenData } from "../types/player_types";
import { EquipmentScreenData } from "../types/equipment_types";

export type EquipmentChangeScreenData = {
    "player": PlayerScreenData;
    "owned_weapons": EquipmentScreenData[];
    "owned_armors": EquipmentScreenData[];
};
