"use client"

import { useState, useEffect, useRef, useCallback, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "../../lib/apiClient";
import { BattleScreenData } from "./types";
import { ColorButton } from "../../components/atoms/button/ColorButton";
import styles from "./BattleScreen.module.css";
import { getHpColor, enemyImageSrc, stageBackgroundSrc } from "./battleUtils";
import { MessageBox } from "../../components/molecules/battle/MessageBox";
import { GaugeBar } from "../../components/molecules/battle/GaugeBar";
import { SpecialCommand } from "@/src/components/Organisms/battle/SpecialCommand";
import { BattleEndPanel } from "@/src/components/Organisms/battle/BattleEndPanel";

type Props = {
    playerId: string;
    stageId: string;
};

type TimingPhase = "ready" | "waiting" | "signal" | "finished";

const TIMING_WAIT_MIN_MS = 800;
const TIMING_WAIT_MAX_MS = 2200;
const TIMING_FAIL_MS = 2000;

function getTimingMultiplier(elapsedMs: number) {
    if (elapsedMs <= 200) return 3.0;
    if (elapsedMs <= 500) return 2.0;
    if (elapsedMs <= 1000) return 1.2;
    if (elapsedMs <= TIMING_FAIL_MS) return 0.8;
    return 0;
}

function getRandomTimingDelayMs() {
    return Math.floor(
        TIMING_WAIT_MIN_MS + Math.random() * (TIMING_WAIT_MAX_MS - TIMING_WAIT_MIN_MS),
    );
}

function updateBackgroundFromData(
    data: BattleScreenData,
    setBackgroundImage: (v: string) => void,
) {
    if (data.battle?.stage?.background_image) {
        setBackgroundImage(data.battle.stage.background_image);
    } else if (data.event?.type === "victory" && data.event.payload.stage?.background_image) {
        setBackgroundImage(data.event.payload.stage.background_image);
    }
}

function getActionKey(data: BattleScreenData) {
    const actionMode = data.action_mode?.active ? data.action_mode : null;
    if (!actionMode) return null;
    return `${actionMode.skill_index}-${actionMode.skill_name}`;
}

export default function BattleScreen(props: Props) {
    const { playerId, stageId } = props;
    const [data, setData] = useState<BattleScreenData | null>(null);
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [itemOpen, setItemOpen] = useState(false);
    const [skillOpen, setSkillOpen] = useState(false);
    const [actionTimeLeft, setActionTimeLeft] = useState<number | null>(null);
    const [actionStarted, setActionStarted] = useState(false);
    const [timingPhase, setTimingPhase] = useState<TimingPhase>("ready");
    const [timingResultText, setTimingResultText] = useState("");
    const [actionFinishing, setActionFinishing] = useState(false);
    const finishingActionRef = useRef(false);
    const activeActionKeyRef = useRef<string | null>(null);
    const timingDelayTimerRef = useRef<number | null>(null);
    const timingFailTimerRef = useRef<number | null>(null);
    const timingSignalAtRef = useRef<number | null>(null);
    const router = useRouter();

    const clearTimingTimers = useCallback(() => {
        if (timingDelayTimerRef.current != null) {
            window.clearTimeout(timingDelayTimerRef.current);
            timingDelayTimerRef.current = null;
        }
        if (timingFailTimerRef.current != null) {
            window.clearTimeout(timingFailTimerRef.current);
            timingFailTimerRef.current = null;
        }
    }, []);

    const applyData = useCallback((next: BattleScreenData) => {
        setData(next);
        updateBackgroundFromData(next, setBackgroundImage);
        const nextActionKey = getActionKey(next);
        const nextActionMode = next.action_mode?.active ? next.action_mode : null;
        if (!nextActionKey || !nextActionMode) {
            clearTimingTimers();
            activeActionKeyRef.current = null;
            timingSignalAtRef.current = null;
            setActionTimeLeft(null);
            setActionStarted(false);
            setTimingPhase("ready");
            setTimingResultText("");
            setActionFinishing(false);
        } else if (activeActionKeyRef.current !== nextActionKey) {
            clearTimingTimers();
            activeActionKeyRef.current = nextActionKey;
            timingSignalAtRef.current = null;
            setActionTimeLeft(nextActionMode.action_type === "spam" ? nextActionMode.duration_seconds : null);
            setActionStarted(false);
            setTimingPhase("ready");
            setTimingResultText("");
            setActionFinishing(false);
            finishingActionRef.current = false;
        }
    }, [clearTimingTimers]);

    const loadBattle = useCallback(() => {
        apiGet(`/api/battle/${playerId}/?stage_id=${stageId}`).then((res: BattleScreenData) => {
            applyData(res);
            setItemOpen(false);
            setSkillOpen(false);
        });
    }, [applyData, playerId, stageId]);

    useEffect(() => {
        loadBattle();
    }, [loadBattle]);

    const handleAttack = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "attack" }).then(applyData);
    };

    const handleDefend = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "defend" }).then(applyData);
    };

    const handleEscape = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "escape" }).then(applyData);
    };

    const handleUseItem = (itemId: string) => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "item", item_id: itemId }).then(applyData);
    };

    const handleUseSkill = (index: number) => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, {
            action: "special",
            special: `skill${index + 1}`,
        }).then(applyData);
    };

    const handleReturn = () => {
        router.push(`/game/battle/home/${playerId}/`);
    };

    const handleContinue = () => {
        loadBattle();
    };

    const battle = data?.battle;
    const enemy = battle?.enemy;
    const actionMode = data?.action_mode?.active ? data.action_mode : null;
    const showCombat = battle != null && data?.event == null;
    const bgStyle = backgroundImage
        ? { backgroundImage: `url("${stageBackgroundSrc(backgroundImage)}")` }
        : undefined;

    const finishAction = useCallback((extraData: Record<string, string> = {}) => {
        if (finishingActionRef.current) return;
        finishingActionRef.current = true;
        clearTimingTimers();
        setActionFinishing(true);
        setTimingPhase("finished");
        apiPost(`/api/battle/${playerId}/action-finish/`, {
            click_count: String(data?.action_mode?.click_count ?? 0),
            ...extraData,
        })
            .then((res: BattleScreenData) => {
                applyData(res);
                setActionTimeLeft(null);
                setActionStarted(false);
                setTimingPhase("ready");
                setTimingResultText("");
                timingSignalAtRef.current = null;
                activeActionKeyRef.current = null;
            })
            .finally(() => {
                setActionFinishing(false);
                finishingActionRef.current = false;
            });
    }, [applyData, clearTimingTimers, data?.action_mode?.click_count, playerId]);

    const handleActionHit = () => {
        if (!actionMode || actionMode.action_type !== "spam" || actionFinishing || finishingActionRef.current) return;
        apiPost(`/api/battle/${playerId}/action-hit/`, {})
            .then((res: BattleScreenData) => {
                if (finishingActionRef.current) return;
                applyData(res);
                if (res.action_hit?.enemy_defeated) {
                    finishAction();
                }
            });
    };

    const handleSpamOverlayClick = () => {
        if (!actionMode || actionMode.action_type !== "spam" || actionFinishing || finishingActionRef.current) return;
        if (!actionStarted) {
            setActionStarted(true);
            setActionTimeLeft(actionMode.duration_seconds);
            return;
        }
        if ((actionTimeLeft ?? 0) <= 0) return;
        handleActionHit();
    };

    const handleSpamOverlayKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        handleSpamOverlayClick();
    };

    const failTimingAction = useCallback((message = "失敗") => {
        if (finishingActionRef.current) return;
        clearTimingTimers();
        setTimingResultText(message);
        finishAction({
            timing_result: "fail",
            timing_multiplier: "0",
        });
    }, [clearTimingTimers, finishAction]);

    const startTimingAction = () => {
        if (!actionMode || actionMode.action_type !== "timing" || actionFinishing || finishingActionRef.current) return;
        setActionStarted(true);
        setTimingPhase("waiting");
        setTimingResultText("集中...");
        timingDelayTimerRef.current = window.setTimeout(() => {
            timingDelayTimerRef.current = null;
            timingSignalAtRef.current = performance.now();
            setTimingPhase("signal");
            setTimingResultText("");
            timingFailTimerRef.current = window.setTimeout(() => {
                timingFailTimerRef.current = null;
                failTimingAction("遅すぎた！");
            }, TIMING_FAIL_MS);
        }, getRandomTimingDelayMs());
    };

    const handleTimingOverlayClick = () => {
        if (!actionMode || actionMode.action_type !== "timing" || actionFinishing || finishingActionRef.current) return;
        if (timingPhase === "ready") {
            startTimingAction();
            return;
        }
        if (timingPhase === "waiting") {
            failTimingAction("早すぎた！");
            return;
        }
        if (timingPhase !== "signal" || timingSignalAtRef.current == null) return;

        const elapsedMs = performance.now() - timingSignalAtRef.current;
        const timingMultiplier = getTimingMultiplier(elapsedMs);
        if (timingMultiplier <= 0) {
            failTimingAction("遅すぎた！");
            return;
        }
        clearTimingTimers();
        setTimingResultText(`${timingMultiplier.toFixed(1)}倍`);
        finishAction({
            timing_result: "success",
            timing_multiplier: timingMultiplier.toString(),
        });
    };

    const handleTimingOverlayKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        handleTimingOverlayClick();
    };

    useEffect(() => {
        if (!actionStarted || !actionMode || actionMode.action_type !== "spam" || actionTimeLeft == null) return;
        if (actionTimeLeft <= 0) return;
        const timerId = window.setTimeout(() => {
            setActionTimeLeft((current) => {
                if (current == null) return current;
                const nextTime = Math.max(0, Number((current - 0.1).toFixed(1)));
                if (nextTime <= 0) {
                    finishAction();
                }
                return nextTime;
            });
        }, 100);

        return () => window.clearTimeout(timerId);
    }, [actionMode, actionStarted, actionTimeLeft, finishAction]);

    useEffect(() => {
        return () => clearTimingTimers();
    }, [clearTimingTimers]);

    return (
        <div className={styles.battleContainer} style={bgStyle}>
            {!data && <p className={styles.loading}>読み込み中…</p>}

            {showCombat && battle && enemy && (
                <>
                    <div className={styles.messageArea}>
                        <MessageBox message={battle.message_history.join("\n")} messageHistory={battle.message_history} />
                    </div>

                    <div className={styles.enemyArea}>
                        <div className={styles.enemyLevel}>LV : {enemy.level}</div>
                        <div
                            className={
                                enemy.is_strong
                                    ? `${styles.enemyName} ${styles.enemyNameStrong}`
                                    : styles.enemyName
                            }
                        >
                            {enemy.name}
                        </div>
                        {enemy.image_url && (
                            <img
                                src={enemyImageSrc(enemy.image_url)}
                                alt={enemy.name}
                                className={styles.enemyImage}
                            />
                        )}
                        <GaugeBar
                            percent={battle.enemy_hp_percent}
                            value={enemy.hp}
                            color={getHpColor}
                            variant="hp"
                            className={styles.enemyHpBarContainer}
                        />
                    </div>

                    <div className={styles.playerArea}>
                        <div
                            className={
                                itemOpen || skillOpen
                                    ? `${styles.playerStatusBox} ${styles.playerStatusBoxWide}`
                                    : styles.playerStatusBox
                            }
                        >
                            {!itemOpen && !skillOpen && (
                                <>
                                    <div className={styles.statusTopRow}>
                                        <div className={styles.playerNameCol}>{battle.player.name}</div>
                                        <div className={styles.statusGauge}>
                                            <span>HP:</span>
                                            <GaugeBar
                                                percent={battle.player_hp_percent}
                                                value={battle.player.total_hp_battle}
                                                color={getHpColor}
                                                variant="hp"
                                                className={styles.statusGaugeBar}
                                            />
                                        </div>
                                        <div className={styles.statusGauge}>
                                            <span>SP:</span>
                                            <GaugeBar
                                                percent={battle.player_sp_percent}
                                                value={battle.player.mp}
                                                variant="sp"
                                                className={styles.statusGaugeBar}
                                            />
                                        </div>
                                    </div>
                                    <div className={styles.statsRow}>
                                        <div className={styles.playerNameCol} />
                                        <div className={styles.statsText}>
                                            ATK:{battle.showplayer_atk} DEF:{battle.showplayer_def}{" "}
                                            SPD:{battle.showplayer_spd}
                                        </div>
                                    </div>
                                    <div className={styles.buttonArea}>
                                        <ColorButton
                                            variant="red"
                                            className={styles.commandButton}
                                            onClick={handleAttack}
                                        >
                                            攻撃
                                        </ColorButton>
                                        <ColorButton
                                            variant="blue"
                                            className={styles.commandButton}
                                            onClick={handleDefend}
                                        >
                                            防御
                                        </ColorButton>
                                        <ColorButton
                                            variant="yellow"
                                            className={styles.commandButton}
                                            onClick={() => {
                                                setItemOpen(false);
                                                setSkillOpen(true);
                                            }}
                                        >
                                            特技
                                        </ColorButton>
                                        <ColorButton
                                            variant="orange"
                                            className={styles.commandButton}
                                            onClick={() => {
                                                setSkillOpen(false);
                                                setItemOpen(true);
                                            }}
                                        >
                                            アイテム
                                        </ColorButton>
                                        <ColorButton
                                            variant="other"
                                            className={styles.commandButton}
                                            onClick={handleEscape}
                                        >
                                            逃げる
                                        </ColorButton>
                                    </div>
                                </>
                            )}

                            {skillOpen && (
                                <SpecialCommand 
                                    mode="skill"
                                    skills={battle.player_skills}
                                    onSelectSkill={handleUseSkill}
                                    onClose={() => setSkillOpen(false)}
                                />
                            )}

                            {itemOpen && (
                                <SpecialCommand
                                    mode="item"
                                    items={battle.player_items}
                                    onSelectItem={handleUseItem}
                                    onClose={() => setItemOpen(false)}
                                />
                            )}
                        </div>
                    </div>
                </>
            )}

            {data?.event && (
                <BattleEndPanel
                    event={data.event}
                    onReturn={handleReturn}
                    onContinue={handleContinue}
                />
            )}

            {showCombat && battle && enemy && actionMode && (
                <div
                    className={styles.actionOverlay}
                    onClick={actionMode.action_type === "spam" ? handleSpamOverlayClick : handleTimingOverlayClick}
                    onKeyDown={actionMode.action_type === "spam" ? handleSpamOverlayKeyDown : handleTimingOverlayKeyDown}
                    role="button"
                    tabIndex={0}
                >
                    <div className={styles.actionTimer}>
                        {actionMode.action_type === "spam"
                            ? (actionTimeLeft ?? actionMode.duration_seconds).toFixed(1)
                            : timingPhase === "signal"
                                ? "！"
                                : "TIMING"}
                    </div>
                    <div className={styles.actionSkillName}>{actionMode.skill_name}</div>
                    {actionMode.action_type === "spam" ? (
                        <>
                            <div className={actionStarted ? styles.actionInstruction : styles.actionStartPrompt}>
                                {actionStarted ? "連打！！" : "画面をクリックして開始"}
                            </div>
                            <div className={styles.actionResult}>
                                {actionMode.click_count} HIT / 合計 {actionMode.total_damage} ダメージ
                            </div>
                            {data.action_hit ? (
                                <div className={styles.actionLastHit}>
                                    +{data.action_hit.damage}
                                </div>
                            ) : null}
                        </>
                    ) : (
                        <div className={styles.timingArea}>
                            <div className={timingPhase === "signal" ? styles.timingSignal : styles.actionStartPrompt}>
                                {timingPhase === "ready" && "画面をクリックして開始"}
                                {timingPhase === "waiting" && "集中..."}
                                {timingPhase === "signal" && "今だ！"}
                                {timingPhase === "finished" && "判定中..."}
                            </div>
                            <div className={styles.timingGuide}>
                                {timingPhase === "ready" && "「！」が出た瞬間を狙おう"}
                                {timingPhase === "waiting" && "まだクリックしない"}
                                {timingPhase === "signal" && "早くクリックするほど高火力"}
                                {timingPhase === "finished" && timingResultText}
                            </div>
                            {timingResultText && timingPhase !== "finished" ? (
                                <div className={styles.actionLastHit}>{timingResultText}</div>
                            ) : null}
                        </div>
                    )}
                </div>
            )}

        </div>
    );
}
