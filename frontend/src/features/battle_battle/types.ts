import { PlayerScreenData } from "../types/player_types";
import { EnemyScreenData } from "../types/enemy_types";
import { StageData } from "../types/stage_types";
import { InventoryItemData } from "../types/item_types";
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
        "player_skills": SkillData[];
        "player_items": InventoryItemData[];
        "stage": StageData,
        "player_hp_percent": number,
        "player_sp_percent": number,
        "enemy_hp_percent": number,
    } | null,
    "event": BattleEvent | null;
    "action_mode"?: ActionModeData | null;
    "action_hit"?: ActionHitData;
    "turn_result"?: TurnResultData;
};

export type TurnStepData = {
    actor: "player" | "enemy";
    message: string;
    before: {
        player_hp: number;
        player_sp: number;
        enemy_hp: number;
    };
    after: {
        player_hp: number;
        player_sp: number;
        enemy_hp: number;
    };
};

export type TurnResultData = {
    player_first: boolean;
    steps: TurnStepData[];
};

export type ActionModeData = {
    active: boolean;
    skill_name: string;
    action_type: "spam" | "timing";
    skill_index: number | null;
    duration_seconds: number;
    click_count: number;
    total_damage: number;
};

export type ActionHitData = {
    damage: number;
    total_damage: number;
    click_count: number;
    enemy_defeated: boolean;
};

export type SkillData = {
    id: number;
    name: string;
    cost: number;
    description: string;
    is_action: boolean | null;
    action_type: "spam" | "timing" | null;
    effects: {
        type: string;
        target: "player" | "enemy";
        multiplier: number;
        stat: "atk" | "def" | "spd" | null;
        turn: number | null;
    }[];
}