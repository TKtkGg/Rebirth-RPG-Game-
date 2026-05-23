import { StageData } from "../types/stage_types";

export type VictoryPayload = {
    gained_exp: number;
    gained_gold: number;
    existLevel: number;
    newLevel: number;
    stage: StageData;
};

export type EscapePayload = {
    message: string;
    escaped: boolean;
    exp_penalty: number;
    gold_penalty: number;
};

export type TohomePayload = {
    message: string;
    redirect_after: boolean;
    recovering: boolean;
};

export type GameoverPayload = {
    message: string;
};

export type ErrorPayload = {
    message: string;
};

export type BattleEvent = 
    | { type: "victory", payload: VictoryPayload }
    | { type: "escape", payload: EscapePayload }
    | { type: "tohome", payload: TohomePayload }
    | { type: "gameover", payload: GameoverPayload }
    | { type: "error", payload: ErrorPayload };