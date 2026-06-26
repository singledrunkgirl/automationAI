const localAssetUrl = (fileName: string): string =>
  `/downloads/${encodeURIComponent(fileName)}`;

export const downloadLinks = {
  windows: localAssetUrl("HackWithAI_0.1.0_x64-setup.exe"),
  linuxDeb: localAssetUrl("HackWithAI_0.1.0_amd64.deb"),
  linuxAppImage: localAssetUrl("HackWithAI_0.1.0_amd64.AppImage"),
  androidApk: localAssetUrl("HackWithAI_0.1.0_android.apk"),
};
