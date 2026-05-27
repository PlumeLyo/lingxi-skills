import { PPTElement, Gradient } from '../../types/slides';
import { ElementRendererOverrides } from './renderers';
/**
 * 生成 PPTX 文件的选项配置
 */
interface GenerateOptions {
    /** PPTX 文件的标题 */
    title?: string;
    /** 幻灯片宽度（英寸） */
    slideWidth?: number;
    /** 幻灯片高度（英寸） */
    slideHeight?: number;
    /** 是否自动调整元素大小以适应幻灯片 */
    autoFit?: boolean;
    /** 根元素宽度（磅） */
    rootWidthPt?: number;
    /** 根元素高度（磅） */
    rootHeightPt?: number;
    /** 幻灯片背景：纯色 HEX 字符串或 Gradient 渐变对象 */
    background?: string | Gradient;
    /** 元素渲染器覆盖 */
    renderers?: ElementRendererOverrides;
}
/**
 * 从PPT元素数组生成PPTX文件Blob
 * @param elements PPT元素数组
 * @param options 生成选项
 * @returns PPTX文件的Blob对象
 */
declare function generatePptxFromElements(elements: PPTElement[], options?: GenerateOptions): Promise<Blob>;
/**
 * 从DOM元素生成PPTX文件Blob
 * @param root 根DOM元素
 * @param options 生成选项
 * @returns PPTX文件的Blob对象
 */
declare function generatePptx(root: Element, options?: GenerateOptions): Promise<Blob>;
/** 多页导出时每一页的数据 */
interface SlideData {
    elements: PPTElement[];
    rootWidthPt: number;
    rootHeightPt: number;
    /** 幻灯片背景：纯色 HEX 字符串或 Gradient 渐变对象 */
    background?: string | Gradient;
}
/**
 * 从多页 SlideData 数组生成包含多张幻灯片的 PPTX Blob
 */
declare function generatePptxMultiSlide(slides: SlideData[], options?: GenerateOptions): Promise<Blob>;
/**
 * 生成并下载PPTX文件
 * @param root 根DOM元素
 * @param fileName 下载的文件名
 * @param options 生成选项
 */
declare function downloadPptx(root: Element, fileName?: string, options?: GenerateOptions): Promise<void>;
export type { GenerateOptions, SlideData };
export { generatePptxFromElements, generatePptxMultiSlide, generatePptx, downloadPptx };
