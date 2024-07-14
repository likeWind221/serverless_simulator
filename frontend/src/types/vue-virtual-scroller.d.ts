declare module "vue-virtual-scroller" {
  import { DefineComponent, Plugin } from "vue";

  interface PluginOptions {
    installComponents?: boolean;
    componentsPrefix?: string;
  }

  const plugin: Plugin & { version: string };

  export const RecycleScroller: DefineComponent<{}, {}, any>;
  export const DynamicScroller: DefineComponent<{}, {}, any>;
  export const DynamicScrollerItem: DefineComponent<{}, {}, any>;

  export function IdState(options?: {
    idProp?: (vm: any) => any;
  }): DefineComponent<{}, {}, any>;

  export default plugin;
}
