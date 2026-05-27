/**
 * ECharts 图表解析 — 类型定义
 *
 * 从 ECharts getOption() 返回值中提取所需的接口，
 * 以及模块间共享的内部辅助类型。
 */
export interface EChartsInstance {
    getOption: () => EChartsOption;
    getModel?: () => {
        getComponent?: (type: string) => {
            option?: {
                elements?: unknown[];
            };
        } | undefined;
    };
}
export interface EChartsOptionSeriesDataItem {
    value?: number | number[];
    name?: string;
    itemStyle?: {
        color?: string | unknown;
    };
    label?: EChartsLabelConfig;
}
export interface EChartsLabelConfig {
    show?: boolean;
    formatter?: string | ((params: {
        dataIndex: number;
        value: unknown;
        data?: unknown;
        name?: string;
    }) => string);
    color?: string;
    fontSize?: number;
    fontWeight?: string | number;
    position?: string;
    rich?: Record<string, {
        fontSize?: number;
        fontWeight?: string;
        color?: string;
    }>;
}
export interface EChartsOptionSeries {
    type?: string;
    name?: string;
    data?: (number | number[] | EChartsOptionSeriesDataItem | null | undefined)[];
    stack?: string;
    barWidth?: string | number;
    barGap?: string | number;
    barCategoryGap?: string | number;
    itemStyle?: {
        color?: string | unknown;
        color0?: string;
        borderColor?: string;
        borderColor0?: string;
        borderWidth?: number;
        opacity?: number;
        shadowBlur?: number;
        shadowColor?: string;
    };
    color?: string | unknown;
    yAxisIndex?: number;
    label?: EChartsLabelConfig;
    emphasis?: {
        label?: EChartsLabelConfig;
    };
    smooth?: boolean;
    symbol?: string;
    symbolSize?: number | ((data: unknown, params?: unknown) => number);
    showSymbol?: boolean;
    lineStyle?: {
        color?: string | unknown;
        width?: number;
        type?: string;
    };
    markPoint?: {
        data?: {
            type?: string;
            name?: string;
        }[];
        itemStyle?: {
            color?: string | unknown;
        };
        symbolSize?: number;
    };
    markLine?: {
        symbol?: string | string[];
        lineStyle?: {
            color?: string;
            width?: number;
            type?: string;
            opacity?: number;
        };
        label?: {
            show?: boolean;
            position?: string;
            formatter?: string;
            color?: string;
            fontSize?: number;
            fontWeight?: string | number;
        };
        data?: ({
            xAxis?: number;
            yAxis?: number;
            label?: {
                show?: boolean;
                position?: string;
                formatter?: string;
                color?: string;
                fontSize?: number;
                fontWeight?: string | number;
            };
            lineStyle?: {
                color?: string;
                width?: number;
                type?: string;
                opacity?: number;
            };
        } | [
            {
                xAxis?: number;
                yAxis?: number;
                coord?: [number, number];
            },
            {
                xAxis?: number;
                yAxis?: number;
                coord?: [number, number];
            }
        ])[];
        silent?: boolean;
    };
    areaStyle?: {
        color?: string | {
            type?: string;
            colorStops?: {
                offset: number;
                color: string;
            }[];
        };
        opacity?: number;
    };
    radius?: string | number | (string | number)[];
    startAngle?: number;
    labelLine?: {
        lineStyle?: {
            color?: string;
        };
    };
}
export interface EChartsOptionAxis {
    type?: string;
    show?: boolean;
    boundaryGap?: boolean | [string, string];
    scale?: boolean;
    data?: string[];
    name?: string;
    nameLocation?: "start" | "middle" | "center" | "end";
    nameTextStyle?: {
        fontSize?: number;
        color?: string;
    };
    min?: number | string;
    max?: number | string;
    position?: string;
    inverse?: boolean;
    splitNumber?: number;
    interval?: number;
    splitLine?: {
        show?: boolean;
        lineStyle?: {
            type?: string;
            width?: number;
            color?: string | string[];
        };
    };
    axisLine?: {
        show?: boolean | "auto";
        lineStyle?: {
            width?: number;
            color?: string;
        };
    };
    axisTick?: {
        show?: boolean | "auto";
    };
    axisLabel?: {
        show?: boolean;
        color?: string;
        fontSize?: number;
        fontWeight?: string | number;
        interval?: number | "auto";
        formatter?: string | ((value: number | string, index?: number) => string);
    };
}
export interface EChartsLegend {
    show?: boolean;
    top?: number | string;
    bottom?: number | string;
    left?: number | string;
    right?: number | string;
    orient?: string;
    textStyle?: {
        fontSize?: number;
        color?: string;
    };
}
export interface EChartsGrid {
    top?: number | string;
    bottom?: number | string;
    left?: number | string;
    right?: number | string;
    containLabel?: boolean;
}
export interface EChartsOptionTitle {
    text?: string;
    textStyle?: {
        color?: string;
        fontSize?: number | string;
        fontFamily?: string;
    };
}
export interface EChartsGraphicStyle {
    text?: string;
    fontSize?: number;
    fontWeight?: string | number;
    fill?: string;
    fontFamily?: string;
}
export interface EChartsGraphicElement {
    type?: string;
    left?: number | string;
    right?: number | string;
    top?: number | string;
    bottom?: number | string;
    style?: EChartsGraphicStyle;
    children?: EChartsGraphicElement[];
    elements?: EChartsGraphicElement[];
}
export interface EChartsVisualMap {
    min?: number;
    max?: number;
    dimension?: number;
    inRange?: {
        color?: string[];
        symbolSize?: [number, number] | number[];
    };
}
export interface EChartsRadarIndicator {
    name?: string;
    max?: number;
}
export interface EChartsRadarComponent {
    indicator?: EChartsRadarIndicator[];
    shape?: string;
    axisName?: {
        fontSize?: number;
        color?: string;
    };
    splitLine?: {
        lineStyle?: {
            width?: number;
            color?: string | string[];
        };
    };
    axisLine?: {
        lineStyle?: {
            width?: number;
            color?: string;
        };
    };
}
export interface EChartsRadarDataItem {
    value?: number[];
    name?: string;
    itemStyle?: {
        color?: string | unknown;
    };
    areaStyle?: {
        opacity?: number;
        color?: string;
    };
    lineStyle?: {
        width?: number;
        type?: string;
        color?: string;
    };
    symbol?: string;
    symbolSize?: number;
}
export interface EChartsOption {
    series?: EChartsOptionSeries[];
    xAxis?: EChartsOptionAxis | EChartsOptionAxis[];
    yAxis?: EChartsOptionAxis | EChartsOptionAxis[];
    title?: EChartsOptionTitle | EChartsOptionTitle[];
    color?: (string | unknown)[];
    legend?: EChartsLegend | EChartsLegend[];
    grid?: EChartsGrid | EChartsGrid[];
    graphic?: EChartsGraphicElement | EChartsGraphicElement[];
    visualMap?: EChartsVisualMap | EChartsVisualMap[];
    radar?: EChartsRadarComponent | EChartsRadarComponent[];
    polar?: unknown | unknown[];
    geo?: unknown | unknown[];
    singleAxis?: unknown | unknown[];
    label?: EChartsLabelConfig;
}
export interface EChartsGlobal {
    getInstanceByDom?: (dom: Element) => EChartsInstance | undefined;
}
export interface StackInfo {
    stack?: string;
    valueAxisIndex?: number;
    data: (number | null)[];
}
export interface SeriesConvertContext {
    domElement: Element;
    palette: (string | unknown)[] | undefined;
    paletteIndexMap: number[];
    isPie: boolean;
}
export type LegendPos = "b" | "t" | "l" | "r";
export interface ComputeGapWidthOption {
    catCount: number;
    widthPx: number;
    heightPx: number;
    grid?: EChartsGrid | EChartsGrid[];
    dir: "col" | "bar";
}
export interface MarkLineStyleInfo {
    color?: string;
    widthPx: number;
    dash: "dash" | "dot" | "solid";
    opacity?: number;
}
