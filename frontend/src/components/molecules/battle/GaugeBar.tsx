import styles from "./GaugeBar.module.css";

type Props = {
    percent: number;
    value: number;
    color?: (percent: number) => string;
    variant: "hp" | "sp";
    className: string;
}

export const GaugeBar = (props: Props) => {
    const { percent, value, color, variant, className } = props;
    return (
        <div className={`${styles.GaugeBarContainer} ${className}`}>
            <div
                className={styles.GaugeBarFill}
                style={{
                    width: `${percent}%`,
                    backgroundColor: variant === "hp" ? color?.(percent) : "rgb(0, 55, 255)",
                }}
            />
            <span className={styles.GaugeBarValue}>{value}</span>
        </div>
    )
}