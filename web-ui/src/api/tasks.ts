import type {
  Task,
  TaskCreateResponse,
  TaskGenerateRequest,
  TaskGenerationJob,
  TaskUpdate,
} from '@/types/task.d.ts'
import { http } from '@/lib/http'

export interface TaskRunRecord {
  run_id: string
  task_id: number
  task_name: string
  started_at: string
  finished_at: string | null
  status: 'running' | 'success' | 'failed' | 'stopped'
  exit_code: number | null
}

export interface TaskHistory {
  task_id: number
  total_runs: number
  success_count: number
  failure_count: number
  stopped_count: number
  running: boolean
  recent_runs: TaskRunRecord[]
}

export async function getTaskHistory(taskId: number): Promise<TaskHistory> {
  return await http(`/api/tasks/history/${taskId}`)
}

export interface TaskPreflightCheck {
  key: string
  label: string
  status: 'pass' | 'error'
  passed: boolean
  detail: string
  fix: string
}

export interface TaskPreflightResponse {
  task_id: number
  task_name: string
  ready: boolean
  checks: TaskPreflightCheck[]
  blocking_count: number
  summary: string
}

export async function getAllTasks(): Promise<Task[]> {
  return await http('/api/tasks')
}

export async function createTaskWithAI(data: TaskGenerateRequest): Promise<TaskCreateResponse> {
  return await http('/api/tasks/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
}

export async function getTaskGenerationJob(jobId: string): Promise<TaskGenerationJob> {
  const result = await http(`/api/tasks/generate-jobs/${jobId}`)
  return result.job
}

export async function updateTask(taskId: number, data: TaskUpdate): Promise<Task> {
  const result = await http(`/api/tasks/${taskId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return result.task
}

export async function startTask(taskId: number): Promise<void> {
  await http(`/api/tasks/start/${taskId}`, { method: 'POST' })
}

export async function preflightTask(taskId: number): Promise<TaskPreflightResponse> {
  return await http(`/api/tasks/preflight/${taskId}`)
}

export async function stopTask(taskId: number): Promise<void> {
  await http(`/api/tasks/stop/${taskId}`, { method: 'POST' })
}

export async function deleteTask(taskId: number): Promise<void> {
  await http(`/api/tasks/${taskId}`, { method: 'DELETE' })
}
