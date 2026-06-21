/**
 * PPTX 生成公共工具
 */
declare const SLIDE_W_INCH = 10;
declare const SLIDE_H_INCH = 5.625;
/**
 * 确保颜色值为不含 # 前缀的大写 HEX 格式。
 * 支持 rgb()/rgba()、#hex、裸 hex 等格式，无法解析时返回 fallback。
 */
declare function ensureHexColor(color: string | undefined, fallback?: string): string;
/**
 * 将文本对齐值映射为 PPTX 生成器支持的对齐枚举
 * @param align 文本对齐值字符串
 * @returns PPTX 生成器支持的对齐值，无效值返回 undefined
 */
declare function mapTextAlign(align: string | undefined): "left" | "right" | "center" | "justify" | undefined;
/**
 * 将垂直对齐值映射为 PPTX 生成器支持的对齐枚举
 * @param valign 垂直对齐值字符串
 * @returns PPTX 生成器支持的垂直对齐值，无效值返回 undefined
 */
declare function mapVerticalAlign(valign: string | undefined): "top" | "middle" | "bottom" | undefined;
/**
 * 从 CSS font-family 列表中取第一个受支持的字体名
 * @param fontFamily CSS font-family 字符串
 * @returns 第一个受支持的字体名，无匹配时返回 undefined
 */
declare function getFirstFontFace(fontFamily: string | undefined): string | undefined;
interface ShadowInput {
    h: number;
    v: number;
    blur: number;
    color: string;
    opacity?: number;
}
declare function buildShadowProps(shadow: ShadowInput | undefined): Record<string, unknown> | undefined;
type CustomPoint = {
    x: number;
    y: number;
    moveTo?: boolean;
} | {
    x: number;
    y: number;
    curve: {
        type: "arc";
        hR: number;
        wR: number;
        stAng: number;
        swAng: number;
    };
} | {
    close: true;
};
/**
 * 根据四角圆角半径构建圆角矩形路径点
 * @param wInch 矩形宽度（英寸）
 * @param hInch 矩形高度（英寸）
 * @param tlPt 左上角圆角半径（磅值）
 * @param trPt 右上角圆角半径（磅值）
 * @param brPt 右下角圆角半径（磅值）
 * @param blPt 左下角圆角半径（磅值）
 * @returns 圆角矩形路径点数组
 */
declare function buildRoundedRectPoints(wInch: number, hInch: number, tlPt: number, trPt: number, brPt: number, blPt: number): CustomPoint[];
/**
 * 判断四角圆角半径是否一致
 * @param tl 左上角圆角半径
 * @param tr 右上角圆角半径
 * @param br 右下角圆角半径
 * @param bl 左下角圆角半径
 * @returns 四角半径是否完全相同
 */
declare function isUniformRadius(tl: number, tr: number, br: number, bl: number): boolean;
interface OutlineInput {
    style?: string;
    width?: number;
    color?: string;
}
declare function buildLineProps(outline: OutlineInput | undefined): Record<string, unknown> | undefined;
export type { ShadowInput, OutlineInput };
export { SLIDE_W_INCH, SLIDE_H_INCH, ensureHexColor, mapTextAlign, mapVerticalAlign, getFirstFontFace, buildShadowProps, buildRoundedRectPoints, isUniformRadius, buildLineProps, };
