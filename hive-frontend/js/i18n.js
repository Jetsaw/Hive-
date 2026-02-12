/**
 * Multi-Language Support Module (i18n)
 * Supports English (EN) and Bahasa Malaysia (MS)
 */

const translations = {
    en: {
        // Header
        'academic_adviser': 'Academic Adviser',
        'online': 'Online',
        'offline': 'Offline',

        // Welcome
        'welcome_title': "Hi, I'm HIVE",
        'welcome_subtitle': 'MMU Academic Adviser',

        // Quick Questions
        'quick_q1': 'What courses are in Year 1?',
        'quick_q2': 'Tell me about Applied AI programme',
        'quick_q3': 'What are the prerequisites?',
        'quick_q4': 'Compare AI vs Robotics',

        // Input
        'input_placeholder': 'Ask me anything about your courses...',
        'disclaimer': 'HIVE CAN MAKE MISTAKES. CROSS-CHECK VIA THE MMU STUDENT PORTAL.',

        // Sidebar
        'chat': 'Chat',
        'history': 'History',
        'settings': 'Settings',
        'admin': 'Admin',
        'new_conversation': 'New Conversation',
        'programme': 'Programme',
        'select_programme': 'Select Programme',
        'compare_courses': 'Compare Courses',
        'view_calendar': 'View Calendar',
        'study_groups': 'Study Groups',
        'give_feedback': 'Give Feedback',
        'export_chat': 'Export Chat',

        // Chat
        'error_message': 'Sorry, I encountered an error. Please try again.',
        'timeout_message': 'Request timed out. Please try again.',
        'network_error': 'Network error. Please check your connection.',
        'new_chat_confirm': 'Start a new conversation? This will clear the current chat.',

        // Export
        'export_title': 'Export Conversation',
        'export_pdf': 'PDF',
        'export_txt': 'TXT',
        'export_json': 'JSON',
        'export_success': 'Conversation exported successfully!',

        // Feedback
        'feedback_title': 'Give Feedback',
        'feedback_prompt': 'How was your experience?',
        'feedback_comment': 'Additional comments (optional)',
        'feedback_submit': 'Submit Feedback',
        'feedback_thanks': 'Thank you for your feedback!',

        // Calendar
        'calendar_title': 'Academic Calendar',
        'current_trimester': 'Current Trimester',
        'upcoming_events': 'Upcoming Events',
        'days_remaining': 'days remaining',

        // Comparison
        'comparison_title': 'Course Comparison',
        'similarities': 'Similarities',
        'differences': 'Differences',

        // Study Groups
        'study_groups_title': 'Study Groups',
        'create_group': 'Create Group',
        'find_partners': 'Find Partners',
        'join_group': 'Join',
        'leave_group': 'Leave',
        'members': 'members',
    },
    ms: {
        // Header
        'academic_adviser': 'Penasihat Akademik',
        'online': 'Dalam Talian',
        'offline': 'Luar Talian',

        // Welcome
        'welcome_title': 'Hai, Saya HIVE',
        'welcome_subtitle': 'Penasihat Akademik MMU',

        // Quick Questions
        'quick_q1': 'Apakah kursus di Tahun 1?',
        'quick_q2': 'Ceritakan tentang program AI Gunaan',
        'quick_q3': 'Apakah prasyarat kursus?',
        'quick_q4': 'Bandingkan AI vs Robotik',

        // Input
        'input_placeholder': 'Tanya saya tentang kursus anda...',
        'disclaimer': 'HIVE MUNGKIN MEMBUAT KESILAPAN. SEMAK SEMULA MELALUI PORTAL PELAJAR MMU.',

        // Sidebar
        'chat': 'Sembang',
        'history': 'Sejarah',
        'settings': 'Tetapan',
        'admin': 'Pentadbir',
        'new_conversation': 'Perbualan Baharu',
        'programme': 'Program',
        'select_programme': 'Pilih Program',
        'compare_courses': 'Bandingkan Kursus',
        'view_calendar': 'Lihat Kalendar',
        'study_groups': 'Kumpulan Belajar',
        'give_feedback': 'Beri Maklum Balas',
        'export_chat': 'Eksport Sembang',

        // Chat
        'error_message': 'Maaf, saya mengalami ralat. Sila cuba lagi.',
        'timeout_message': 'Permintaan tamat masa. Sila cuba lagi.',
        'network_error': 'Ralat rangkaian. Sila semak sambungan anda.',
        'new_chat_confirm': 'Mulakan perbualan baharu? Ini akan memadamkan sembang semasa.',

        // Export
        'export_title': 'Eksport Perbualan',
        'export_pdf': 'PDF',
        'export_txt': 'TXT',
        'export_json': 'JSON',
        'export_success': 'Perbualan berjaya dieksport!',

        // Feedback
        'feedback_title': 'Beri Maklum Balas',
        'feedback_prompt': 'Bagaimana pengalaman anda?',
        'feedback_comment': 'Komen tambahan (pilihan)',
        'feedback_submit': 'Hantar Maklum Balas',
        'feedback_thanks': 'Terima kasih atas maklum balas anda!',

        // Calendar
        'calendar_title': 'Kalendar Akademik',
        'current_trimester': 'Trimester Semasa',
        'upcoming_events': 'Acara Akan Datang',
        'days_remaining': 'hari berbaki',

        // Comparison
        'comparison_title': 'Perbandingan Kursus',
        'similarities': 'Persamaan',
        'differences': 'Perbezaan',

        // Study Groups
        'study_groups_title': 'Kumpulan Belajar',
        'create_group': 'Cipta Kumpulan',
        'find_partners': 'Cari Rakan',
        'join_group': 'Sertai',
        'leave_group': 'Keluar',
        'members': 'ahli',
    }
};

let currentLanguage = localStorage.getItem('hive_language') || 'en';

/**
 * Get translated string
 */
export function t(key) {
    return (translations[currentLanguage] && translations[currentLanguage][key]) || translations.en[key] || key;
}

/**
 * Get current language
 */
export function getLanguage() {
    return currentLanguage;
}

/**
 * Set language and update UI
 */
export function setLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        localStorage.setItem('hive_language', lang);
        updatePageTranslations();
        return true;
    }
    return false;
}

/**
 * Toggle between EN and MS
 */
export function toggleLanguage() {
    const newLang = currentLanguage === 'en' ? 'ms' : 'en';
    setLanguage(newLang);
    return newLang;
}

/**
 * Update all translatable elements on the page
 */
function updatePageTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });
}

/**
 * Initialize i18n on page load
 */
export function initI18n() {
    updatePageTranslations();
}
