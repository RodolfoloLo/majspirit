import axios from "axios";

import { generateRequestId } from "../lib/requestId";
import { getStoredToken } from "../lib/token";
import type { ApiEnvelope } from "../types/api";

const defaultBase = "/api/v1";

//这个函数作用是创建一个axios实例(http),并设置默认的baseURL、timeout和headers等配置.同时,通过使用请求拦截器(interceptors.request.use),可以在每个请求发送之前添加一些公共的逻辑,比如添加请求ID和授权头.这样就可以确保每个请求都包含必要的信息,并且可以统一处理API响应. --- IGNORE ---
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultBase,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

http.interceptors.request.use((config) => {
  const token = getStoredToken();
  const headers = config.headers;

  headers.set("X-Request-Id", generateRequestId());
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return config;
});

//这个函数作用是处理API响应.它接受一个Promise对象(promise),该对象解析为一个包含data属性的响应对象.函数首先检查响应数据是否符合ApiEnvelope的结构,如果是,则根据code字段判断请求是否成功,并返回data字段的内容;如果不是,则直接返回响应数据.通过使用这个函数,可以统一处理API响应,并根据code字段判断请求是否成功. --- IGNORE ---
export async function unwrap<T>(promise: Promise<{ data: unknown }>): Promise<T> {
  const response = await promise;
  const payload = response.data as Partial<ApiEnvelope<T>> | T;

  if (
    payload &&
    typeof payload === "object" &&
    "code" in payload &&
    "data" in payload
  ) {
    const envelope = payload as ApiEnvelope<T>;
    if (envelope.code !== 0) {
      throw new Error(envelope.message || "业务请求失败");
    }
    return envelope.data;
  }

  return payload as T;
}

//这个文件定义了一个基于axios的HTTP客户端,并提供了一个unwrap函数来处理API响应.unwrap函数会检查响应是否符合ApiEnvelope的结构,如果是,则根据code字段判断请求是否成功,并返回data字段的内容;如果不是,则直接返回响应数据.
//什么是ApiEnvelope?它是一个接口,定义了API响应的标准结构,包含code、message、request_id和data字段.通过使用这个接口,可以统一处理API响应,并根据code字段判断请求是否成功.
//axios是一个流行的HTTP客户端库,它提供了丰富的功能来发送HTTP请求和处理响应.通过创建一个axios实例(http),可以设置默认的baseURL、timeout和headers等配置.同时,通过使用请求拦截器(interceptors.request.use),可以在每个请求发送之前添加一些公共的逻辑,比如添加请求ID和授权头.这样就可以确保每个请求都包含必要的信息,并且可以统一处理API响应.