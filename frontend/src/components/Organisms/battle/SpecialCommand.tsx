import styles from "./SpecialCommand.module.css";
import { SkillData } from "@/src/features/battle_battle/types";
import { InventoryItemData } from "@/src/features/types/item_types";
import { ColorButton } from "../../atoms/button/ColorButton";

type Props = {
    mode: "skill" | "item";
    skills?: SkillData[];
    items?: InventoryItemData[];
    onSelectSkill?: (index: number) => void;
    onSelectItem?: (itemId: string) => void;
    onClose: () => void;
}

export const SpecialCommand = (props: Props) => {
    const { mode, skills, items, onSelectSkill, onSelectItem, onClose } = props;

    return (
        <div className={styles.buttonArea}>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%" }}>
                {mode === "skill" && (
                    <>
                        <p className={styles.subPanelTitle}>特技</p>
                        <div className={styles.commandList}>
                            {skills?.map((skill, index) =>
                                skill.is_action ? null : (
                                    <ColorButton
                                        key={index}
                                        variant="yellow"
                                        className={styles.skillButton}
                                        onClick={() => onSelectSkill?.(index)}
                                    >
                                        {skill.name} (SP: {skill.cost})
                                    </ColorButton>
                                ),
                            )}
                        </div>
                    </>
                )}
                {mode === "item" && (
                    <>
                        <p className={styles.subPanelTitle}>アイテム</p>
                        <div className={styles.commandList}>
                            {items?.length === 0 ? (
                                <div className={styles.itemEmpty}>アイテムがありません</div>
                            ) : (
                                items?.map((inv) => (
                                    <ColorButton
                                        key={inv.id}
                                        variant="orange"
                                        className={styles.itemButton}
                                        onClick={() =>
                                            onSelectItem?.(inv.item.id.toString())
                                        }
                                    >
                                        {inv.item.name}
                                        <br />
                                        (×{inv.quantity})
                                    </ColorButton>
                                ))
                            )}
                        </div>
                    </>
                )}
                <ColorButton
                    variant="other"
                    className={styles.returnButton}
                    onClick={onClose}
                >
                    戻る
                </ColorButton>
            </div>
        </div>
    )
}