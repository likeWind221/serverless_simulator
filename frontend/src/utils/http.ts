import service from './request'
import axios from 'axios'


export function post(url: string, data = {}, params = {}) {
  return new Promise((resolve, reject) => {
    service({
      url,
      method: 'post',
      data: JSON.stringify(data),
      params,
      headers: { 'Content-Type': 'application/json' },
      transformRequest: []
    })
      .then((res: any) => resolve(res.data))
      .catch((err: any) => reject(err))
  })
}
export function put(url: string, data = {}, params = {}) {
  return new Promise((resolve, reject) => {
    service({
      url,
      method: 'put',
      data: JSON.stringify(data),
      params,
      headers: { 'Content-Type': 'application/json' },
      transformRequest: []
    })
      .then((res: any) => resolve(res))
      .catch((err: any) => reject(err))
  })
}
export function get(url: string, params?: any) {
  return new Promise((resolve, reject) => {
    service
      .get(url, { params: params })
      .then((res: any) => resolve(res))
      .catch((err: any) => reject(err))
  })
}
export function del(url: string, data?: any){
  return new Promise((resolve, reject) => {
    service
      .delete(url, { data: data })
      .then((res: any) => resolve(res))
      .catch((err: any) => reject(err))
  })
}
