import styles from './button.module.css'

export const PrimaryButton = ({ children, onClick, disabled }: { children: React.ReactNode, onClick: () => void, disabled?: boolean }) => {
    return(
        <button type="button" className={`${styles.primaryButton} ${disabled ? styles.disabled : ""}`} onClick={onClick} disabled={disabled}>
            {children}
        </button>
    )
}