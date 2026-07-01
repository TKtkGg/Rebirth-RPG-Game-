import { ShopDisplayItem } from "@/src/features/shop/types";
import styles from "./Tooltip.module.css";

type Props = {
    tooltip: {
        item: ShopDisplayItem;
        x: number;
        y: number;
    };
}

export function Tooltip(props: Props) {
    const { tooltip } = props;

    const renderTooltipStats = (item: ShopDisplayItem) => {
        if (item.type === "item") {
            const targetName = item.target === "hp" ? "HP" : "SP";
            return (
                <div className={styles.statLine}>
                    <span className={styles.statPositive}>
                        {targetName} : +{item.effect_amount}
                    </span>
                </div>
            );
        }

        const statLines = [
            { label: "HP", value: item.hp_bonus },
            { label: "ATK", value: item.atk_bonus },
            { label: "DEF", value: item.def_bonus },
            { label: "SPD", value: item.spd_bonus },
        ].filter((stat) => stat.value !== 0);

        return statLines.map((stat) => (
            <div className={styles.statLine} key={`${item.id}-${stat.label}`}>
                <span className={stat.value > 0 ? styles.statPositive : styles.statNegative}>
                    {stat.label} : {stat.value > 0 ? "+" : ""}
                    {stat.value}
                </span>
            </div>
        ));
    };

    return (
        <div
            className={styles.itemTooltip}
            style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
        >
            <div className={styles.tooltipName}>{tooltip.item.name}</div>
            <div className={styles.tooltipDescription}>
                {tooltip.item.description || "説明なし"}
            </div>
            <div className={styles.tooltipStats}>{renderTooltipStats(tooltip.item)}</div>
        </div>
    )
}