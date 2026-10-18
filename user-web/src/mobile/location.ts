import { Capacitor } from "@capacitor/core";
import { Geolocation } from "@capacitor/geolocation";
export async function currentLocation() {
  if (Capacitor.isNativePlatform()) {
    try {
      let permissions = await Geolocation.checkPermissions();
      if (
        permissions.location !== "granted" &&
        permissions.coarseLocation !== "granted"
      )
        permissions = await Geolocation.requestPermissions({
          permissions: ["location"],
        });
      if (
        permissions.location !== "granted" &&
        permissions.coarseLocation !== "granted"
      )
        throw new Error("尚未允许定位，请在系统设置中允许位置权限后重试");
      return await Geolocation.getCurrentPosition({
        enableHighAccuracy: permissions.location === "granted",
        timeout: 15000,
        maximumAge: 10000,
      });
    } catch (error) {
      const code = (error as { code?: string }).code;
      const messages: Record<string, string> = {
        "OS-PLUG-GLOC-0003": "尚未允许定位，请在系统设置中允许位置权限后重试",
        "OS-PLUG-GLOC-0007": "设备定位服务未开启，请开启后重试",
        "OS-PLUG-GLOC-0009": "尚未开启设备定位服务，请开启后重试",
        "OS-PLUG-GLOC-0010": "定位超时，请移至信号较好的位置后重试",
        "OS-PLUG-GLOC-0017": "设备定位与网络均已关闭，请开启定位服务后重试",
      };
      if (code)
        throw new Error(
          messages[code] || "定位暂时不可用，请检查设备定位服务后重试",
        );
      throw error;
    }
  }
  return new Promise<GeolocationPosition>((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("当前设备暂不支持定位"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      resolve,
      (error) =>
        reject(
          new Error(
            error.code === 1
              ? "尚未允许定位，请允许位置权限后重试"
              : "定位暂时不可用，请检查定位服务后重试",
          ),
        ),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 },
    );
  });
}
export function distanceMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
) {
  const rad = (n: number) => (n * Math.PI) / 180;
  const a =
    Math.sin(rad(lat2 - lat1) / 2) ** 2 +
    Math.cos(rad(lat1)) *
      Math.cos(rad(lat2)) *
      Math.sin(rad(lon2 - lon1) / 2) ** 2;
  const bounded = Math.min(1, Math.max(0, a));
  return Math.round(
    6371000 * 2 * Math.atan2(Math.sqrt(bounded), Math.sqrt(1 - bounded)),
  );
}
