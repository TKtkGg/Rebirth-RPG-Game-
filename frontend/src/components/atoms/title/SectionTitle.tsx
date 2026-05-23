import styles from './title.module.css'

export const SectionTitle = ({ title, className }: { title: string, className?: string }) => {
    return(
        <div className={`${styles.sectionTitle} ${className || ''}`}>
            {title}
        </div>
    )
}