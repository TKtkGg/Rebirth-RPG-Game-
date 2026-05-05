import styles from './StatusRow.module.css';

export const StatusRow = ({ label, action }: { label: React.ReactNode, action?: React.ReactNode }) => {
    return (
        <div className={styles.statusRow}>
            <span className={styles.statusLabel}>{label}</span>
            {action ? <span>{action}</span> : null}
        </div>
    )
}