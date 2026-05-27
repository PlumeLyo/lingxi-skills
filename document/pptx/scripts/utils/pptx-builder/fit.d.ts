import { PPTElement } from '../../types/slides';
/**
 * 将元素集合等比缩放并居中到指定幻灯片尺寸
 */
declare function fitElementsToSlide(elements: PPTElement[], rootWidthPt: number, rootHeightPt: number, slideWidthInch: number, slideHeightInch: number): PPTElement[];
export { fitElementsToSlide };
