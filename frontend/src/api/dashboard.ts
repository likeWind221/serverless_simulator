import { post, get, put, del } from '@/utils/http'

export const execute_model = (params:any) => post('/api/run_model',params)
export const stop_model = () => post('/api/stop_model')
export const get_model_status = () => get('/api/status')