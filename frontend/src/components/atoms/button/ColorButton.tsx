import styles from './button.module.css'

export const ColorButton = ({ children, onClick, variant, disabled, className }: { children: React.ReactNode, onClick: () => void, variant: 'red' | 'blue' | 'yellow' | 'brown' | 'other', disabled?: boolean, className?: string }) => {
    return(
        <button type="button" className={styles.colorButton + ' ' + styles[variant] + ' ' + (className ?? '')} onClick={onClick} disabled={disabled}>
            {children}
        </button>
    )
}