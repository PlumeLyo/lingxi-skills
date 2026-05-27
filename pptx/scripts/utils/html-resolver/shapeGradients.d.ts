import { Gradient } from '../../types/slides';
type RepeatingLinearGradientAxis = "x" | "y";
interface RepeatingLinearGradientStop {
    pos: number;
    color: string;
    opacity?: number;
}
interface RepeatingLinearGradient {
    angle: number;
    axis?: RepeatingLinearGradientAxis;
    reverse?: boolean;
    stops: RepeatingLinearGradientStop[];
}
/**
 * 从字符串中提取指定函数名的括号内容（支持嵌套括号）
 * @param source 源字符串
 * @param functionName 函数名
 * @returns 括号内的内容，未找到则返回 undefined
 */
declare function extractFunctionContent(source: string, functionName: string): string | undefined;
/**
 * 按逗号分割渐变参数（跳过嵌套括号内的逗号）
 * @param content 渐变参数字符串
 * @returns 分割后的参数片段数组
 */
declare function splitGradientParts(content: string): string[];
/**
 * 拆分单个 gradient stop 的颜色与位置。
 * @param stop 单个 stop 字符串
 * @returns 拆分后的颜色与位置
 */
declare function splitGradientStop(stop: string): {
    color: string;
    position?: string;
};
/**
 * 解析 linear-gradient。
 * @param backgroundImage CSS background-image 字符串
 * @param element 目标元素
 * @returns 解析后的线性渐变对象，解析失败则返回 undefined
 */
declare function resolveLinearGradient(backgroundImage: string, element?: Element): Gradient | undefined;
/**
 * 解析 repeating-linear-gradient 为重复条纹规格。
 * 仅支持能被归纳为水平/垂直条纹的 0/90/180/270 度方向。
 * @param backgroundImage CSS background-image 字符串
 * @param element 目标元素
 * @param rectSize 元素尺寸（像素）
 * @returns 重复渐变规格，无法解析则返回 undefined
 */
declare function parseRepeatingLinearGradient(backgroundImage: string, element: Element, rectSize: {
    width: number;
    height: number;
}): RepeatingLinearGradient | undefined;
/**
 * 从 background-image 解析渐变（线性或径向）
 * @param backgroundImage CSS background-image 字符串
 * @returns 解析后的渐变对象，非渐变或解析失败则返回 undefined
 */
declare function resolveBackgroundGradient(backgroundImage: string | null | undefined, element?: Element): Gradient | undefined;
/**
 * 将渐变 stop 的半透明颜色与底层背景色进行 alpha compositing。
 * CSS 中 background-color 在 background-image 下方，渐变透明处会透出底色。
 * OOXML 不支持"纯色 + 渐变叠加"，因此需要在解析阶段将底色合成进渐变 stop。
 */
declare function compositeGradientOverBackground(gradient: Gradient, bgHex: string): Gradient;
export { resolveBackgroundGradient, resolveLinearGradient, compositeGradientOverBackground, splitGradientParts, extractFunctionContent, splitGradientStop, };
export type { RepeatingLinearGradientAxis, RepeatingLinearGradientStop, RepeatingLinearGradient, };
export { parseRepeatingLinearGradient };
