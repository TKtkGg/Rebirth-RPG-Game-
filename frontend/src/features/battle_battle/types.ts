import { PlayerScreenData } from "../types/player_types";
import { EnemyScreenData } from "../types/enemy_types";
import { StageData } from "../types/stage_types";
import { ItemScreenData } from "../types/item_types";
import { BattleEvent } from "./event_types";

export type BattleScreenData = {
    "battle": {
        "player": PlayerScreenData,
        "enemy": EnemyScreenData | null,
        "message_history": string[],
        "showplayer_atk": number,
        "showplayer_def": number,
        "showplayer_spd": number,
        "buffs": {
            "player": Record<string, unknown>,
        },
        "showenemy_atk": number,
        "showenemy_def": number,
        "showenemy_spd": number,
        "debuffs": {
            "player": Record<string, unknown>,
        },
        "player_skills": {
            "id": number;
            "name": string;
            "cost": number;
            "description": string;
            "is_action": boolean | null;
            "action_type": "spam" | "timing" | null;
            "effects": {
                "type": string;
                "target": "player" | "enemy";
                "multiplier": number;
                "stat": "atk" | "def" | "spd" | null;
                "turn": number | null;
            }[];
        }[];
        "player_items": {
            "id": number;
            "item": ItemScreenData;
            "quantity": number;
        }[];
        "stage": StageData,
        "player_hp_percent": number,
        "player_sp_percent": number,
        "enemy_hp_percent": number,
    } | null,
    "event": BattleEvent | null;
};  