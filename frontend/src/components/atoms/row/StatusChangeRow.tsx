import styles from './StatusChangeRow.module.css';

type Props = {
    label: string;
    value: string | number;
    changeText?: string;
}

export default function StatusChangeRow(props: Props) {
    const { label, value, changeText } = props;

    return (
        <div className={styles.statItem}>
            <span className={styles.statLabel}>{label}:</span>
            <div className={styles.statValueBlock}>
                <div className={styles.statValue}>{value}</div>
                <div className={styles.statChange}>
                    {changeText}
                </div>
            </div>
        </div>
    );
}