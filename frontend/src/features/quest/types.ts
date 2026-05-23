import { PlayerScreenData } from "../types/player_types";

export type QuestItem = {
    "id": number;
    "quest_template": {
        "title": string;
        "description": string;
        "condition_type": string;
        "condition_target": string;
        "progress_max": number;
        "reward_exp": number;
        "reward_gold": number;
    }
    "progress_current": number;
    "is_claimed": boolean;
    "is_completed": boolean;
}

export type QuestScreenData = {
    "player": PlayerScreenData;
    "life_quests": (QuestItem | null)[];
    "account_quests": (QuestItem | null)[]; 
    "is_guest": boolean;
}