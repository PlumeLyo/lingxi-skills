import { PPTElement } from '../../types/slides';
import { OoxmlPresentation } from './ooxmlPackage';
import { OoxmlSlide } from './ooxml/xmlSlide';
import { XmlRenderable } from './ooxml/types';
/**
 * 从PPT元素中提取指定类型的元素
 */
type ElementOfType<K extends PPTElement["type"]> = Extract<PPTElement, {
    type: K;
}>;
/**
 * 元素渲染器映射，每个元素类型对应一个渲染函数
 */
type ElementRendererMap = {
    [K in PPTElement["type"]]: (slide: OoxmlSlide, element: ElementOfType<K>, presentation: OoxmlPresentation) => XmlRenderable[] | Promise<XmlRenderable[]>;
};
/**
 * 元素渲染器覆盖，可选择性地覆盖默认渲染器
 */
type ElementRendererOverrides = Partial<ElementRendererMap>;
/**
 * 默认渲染器映射，可按元素类型覆盖
 */
declare const defaultElementRenderers: ElementRendererMap;
/**
 * 将PPT元素添加到幻灯片中
 * @param slide 幻灯片对象
 * @param element 要添加的PPT元素
 * @param presentation 生成器实例
 * @param overrides 可选的渲染器覆盖
 */
declare function addElementToSlide(slide: OoxmlSlide, element: PPTElement, presentation: OoxmlPresentation, overrides?: ElementRendererOverrides): Promise<void>;
export type { ElementRendererMap, ElementRendererOverrides };
export { defaultElementRenderers, addElementToSlide };
