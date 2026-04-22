import { PlayerScreenData } from "../types/player_types";

type StageData = {
    "id": number;
    "name": string;
    "unlock_level": number;
    "background_image": string;
    "min_enemy_level": number;
    "max_enemy_level": number;
    "order": number;
}

export type StagesScreenData = {
    "player": PlayerScreenData;
    "stages": StageData[];
}