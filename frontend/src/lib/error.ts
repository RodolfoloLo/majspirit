import axios from "axios";

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const fromApi =
      (error.response?.data?.message as string | undefined) ||
      (error.response?.data?.detail as string | undefined);

    if (fromApi) {
      return fromApi;
    }

    if (error.code === "ECONNABORTED") {
      return "请求超时，请稍后重试";
    }

    if (!error.response) {
      return "网络异常，请检查后端是否启动";
    }

    return `请求失败（${error.response.status}）`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "未知错误";
}
