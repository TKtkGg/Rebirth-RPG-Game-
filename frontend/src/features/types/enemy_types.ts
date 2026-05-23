import { EquipmentScreenData } from "./equipment_types";
import { StagesScreenData } from "./stage_types";

export type EnemyScreenData = {
    "id": number;
    "name": string;
    "level": number;
    "max_hp": number;
    "hp": number;
    "atk": number;
    "defense": number;
    "spd": number;
    "exp": number;
    "drop_gold": number;
    "is_defeated": boolean;
    "is_strong": boolean;
    "appear_level": number;
    "base_max_hp": number;
    "base_atk": number;
    "base_def": number;
    "base_spd": number;
    "base_exp": number;
    "drop_gold_base": number;
    "drop_equipment": EquipmentScreenData[];
    "stages": StagesScreenData[];
}