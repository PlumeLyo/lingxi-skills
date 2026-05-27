import { OoxmlSlide } from './xmlSlide';
interface PresentationXmlInput {
    title: string;
    slideWidth: number;
    slideHeight: number;
    slides: OoxmlSlide[];
}
interface ChartPartInfo {
    chartFileName: string;
    excelFileName: string;
}
declare function buildContentTypesXml(slides: OoxmlSlide[], imageExts: string[], charts?: ChartPartInfo[]): string;
declare function buildRootRelsXml(): string;
declare function buildPresentationXml(input: PresentationXmlInput): string;
declare function buildPresentationRelsXml(slides: OoxmlSlide[]): string;
declare function buildCorePropsXml(title: string): string;
declare function buildAppPropsXml(slideCount: number): string;
declare function buildSlideMasterXml(): string;
declare function buildSlideMasterRelsXml(): string;
declare function buildSlideLayoutXml(): string;
declare function buildSlideLayoutRelsXml(): string;
declare function buildThemeXml(): string;
declare function buildPresPropsXml(): string;
declare function buildViewPropsXml(): string;
declare function buildTableStylesXml(): string;
export { buildContentTypesXml, buildRootRelsXml, buildPresentationXml, buildPresentationRelsXml, buildCorePropsXml, buildAppPropsXml, buildSlideMasterXml, buildSlideMasterRelsXml, buildSlideLayoutXml, buildSlideLayoutRelsXml, buildThemeXml, buildPresPropsXml, buildViewPropsXml, buildTableStylesXml, };
