// A WebP image with a JPG fallback from /assets.
export default function Pic({ name, alt, className = "", width, height, eager = false, ...rest }) {
  return (
    <picture className={className}>
      <source srcSet={`/assets/${name}.webp`} type="image/webp" />
      <img src={`/assets/${name}.jpg`} alt={alt} width={width} height={height}
        loading={eager ? "eager" : "lazy"} decoding="async" {...rest} />
    </picture>
  );
}
