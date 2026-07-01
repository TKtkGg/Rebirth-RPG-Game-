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
    const [actionFinishing, setActionFinishing] = useState(false);
    const finishingActionRef = useRef(false);
    const activeActionKeyRef = useRef<string | null>(null);
    const router = useRouter();

    const applyData = useCallback((next: BattleScreenData) => {
        setData(next);
        updateBackgroundFromData(next, setBackgroundImage);
        const nextActionKey = getActionKey(next);
        const nextActionMode = next.action_mode?.active ? next.action_mode : null;
        if (!nextActionKey || !nextActionMode) {
            activeActionKeyRef.current = null;
            setActionTimeLeft(null);
            setActionStarted(false);
            setActionFinishing(false);
        } else if (activeActionKeyRef.current !== nextActionKey) {
            activeActionKeyRef.current = nextActionKey;
            setActionTimeLeft(nextActionMode.duration_seconds);
            setActionStarted(false);
            setActionFinishing(false);
            finishingActionRef.current = false;
        }
    }, []);

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
        setActionFinishing(true);
        apiPost(`/api/battle/${playerId}/action-finish/`, {
            click_count: String(data?.action_mode?.click_count ?? 0),
            ...extraData,
        })
            .then((res: BattleScreenData) => {
                applyData(res);
                setActionTimeLeft(null);
                setActionStarted(false);
                activeActionKeyRef.current = null;
            })
            .finally(() => {
                setActionFinishing(false);
                finishingActionRef.current = false;
            });
    }, [applyData, data?.action_mode?.click_count, playerId]);

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

    const handleTimingResult = (success: boolean) => {
        finishAction({
            timing_result: success ? "success" : "fail",
            timing_multiplier: success ? "1.5" : "0",
        });
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
                    onClick={actionMode.action_type === "spam" ? handleSpamOverlayClick : undefined}
                    onKeyDown={actionMode.action_type === "spam" ? handleSpamOverlayKeyDown : undefined}
                    role={actionMode.action_type === "spam" ? "button" : undefined}
                    tabIndex={actionMode.action_type === "spam" ? 0 : undefined}
                >
                    <div className={styles.actionTimer}>
                        {actionMode.action_type === "spam"
                            ? (actionTimeLeft ?? actionMode.duration_seconds).toFixed(1)
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
                        <div className={styles.timingActions}>
                            <ColorButton
                                variant="yellow"
                                className={styles.timingButton}
                                onClick={() => handleTimingResult(true)}
                            >
                                成功
                            </ColorButton>
                            <ColorButton
                                variant="other"
                                className={styles.timingButton}
                                onClick={() => handleTimingResult(false)}
                            >
                                失敗
                            </ColorButton>
                        </div>
                    )}
                </div>
            )}

        </div>
    );
}
