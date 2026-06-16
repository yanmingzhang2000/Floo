export interface User {
  user_id: number
  username: string
  nickname: string
  email?: string
  avatar_url?: string
}

export interface UserPreference {
  difficulty_level: string
  theme_type: string
  daily_goal_minutes: number
}

export interface WordItem {
  word: string
  phonetic?: string
  meaning: string
  usage?: string
}

export interface LearningContent {
  id: number
  content_date: string
  title: string
  article: string
  translation?: string
  audio_url?: string
  difficulty_level: string
  theme_type: string
  words: WordItem[]
  content_type: string
}

export interface TodayContentList {
  theme: string
  daily_goal_minutes: number
  contents: LearningContent[]
}

export interface ReviewTask {
  content_id: number
  title: string
  review_stage: number
  last_accuracy: number
  next_review_at: string
}

export interface MemoryProgress {
  content_id: number
  title: string
  review_stage: number
  last_accuracy: number
  next_review_at: string | null
  is_mastered: boolean
  total_review_count: number
}

export interface DictationDiff {
  type: 'missing' | 'wrong' | 'extra'
  expected: string
  actual: string
}

export interface DictationFeedback {
  score: number
  summary: string
  diffs: DictationDiff[]
  suggestions: string[]
}

export interface DictationResult {
  dictation_id: number
  accuracy_rate: number
  feedback: DictationFeedback
  earned_points: number
  next_review_at?: string
  review_stage: number
}

export interface DictationHistory {
  dictation_id: number
  content_id?: number
  content_title?: string
  accuracy_rate: number
  time_spent_seconds?: number
  earned_points: number
  created_at: string
}

export interface CheckinCalendar {
  user_id: number
  year: number
  month: number
  checked_dates: string[]
  available_points: number
  current_streak_days: number
}

export interface CheckinResponse {
  checkin: {
    checkin_id: number
    checkin_date: string
    completed_count: number
    earned_points: number
    note?: string
  }
  available_points: number
  current_streak_days: number
}

export interface WeeklySummary {
  year_week: string
  total_checkin_days: number
  total_learned_count: number
  avg_accuracy_rate: number
  total_earned_points: number
  weekly_review_status: number
}

export interface PointAccount {
  total_earned_points: number
  available_points: number
  total_consumed_points: number
  current_streak_days: number
  max_streak_days: number
}

export interface Character {
  character_id: number
  name: string
  meaning: string
  image_url?: string
  rarity: 'common' | 'rare' | 'legendary'
  description?: string
  count: number
}

export interface BoxResult {
  character_id: number
  name: string
  meaning: string
  image_url?: string
  rarity: string
  description?: string
  is_new: boolean
}
