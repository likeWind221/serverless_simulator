import { post, get, put, del } from '@/utils/http'

export const getResult = () => get('/api/result')
export const getAppStatus = (data: any) => post('/api/app_status', data)
export const deleteResult = (data: any) => del('/api/delete_result', data)