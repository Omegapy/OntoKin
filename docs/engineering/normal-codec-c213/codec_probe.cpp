/* SPDX-FileCopyrightText: 2026 OntoKin contributors
 * SPDX-FileCopyrightText: Blender Authors
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 * Isolated characterization support for selected Blender v4.3.2 codec bodies.
 * No Blender runtime, fan construction, mesh averaging, or importer is linked.
 */
#include <algorithm>
#include <array>
#include <cfloat>
#include <cfenv>
#include <climits>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

#define MINLINE inline
#define LNOR_SPACE_TRIGO_THRESHOLD (1.0f - 1e-4f)

namespace blender {
struct float3 {
  float values[3];
  float3() = default;
  explicit float3(float value) : values{value, value, value} {}
  float3(float x, float y, float z) : values{x, y, z} {}
  float &operator[](int index) { return values[index]; }
  const float &operator[](int index) const { return values[index]; }
  operator float *() { return values; }
  operator const float *() const { return values; }
};
struct short2 {
  short values[2];
  short2() = default;
  explicit short2(short value) : values{value, value} {}
  short2(short x, short y) : values{x, y} {}
  short &operator[](int index) { return values[index]; }
  const short &operator[](int index) const { return values[index]; }
};
inline float3 operator+(const float3 &a, const float3 &b)
{
  return {a[0] + b[0], a[1] + b[1], a[2] + b[2]};
}
inline float3 operator*(const float3 &a, float b)
{
  return {a[0] * b, a[1] * b, a[2] * b};
}
inline float3 operator/(const float3 &a, float b)
{
  return {a[0] / b, a[1] / b, a[2] / b};
}
namespace math {
namespace numbers {
constexpr double pi = 3.141592653589793238462643383279502884;
}
// Scalar specialization of BLI_math_vector.hh dot<float,3>, same operation order.
inline float dot(const float3 &a, const float3 &b)
{
  float result = a[0] * b[0];
  for (int i = 1; i < 3; i++) {
    result += a[i] * b[i];
  }
  return result;
}
// Scalar specialization of normalize_and_get_length<float,3> and normalize.
inline float3 normalize(const float3 &v)
{
  float out_length = dot(v, v);
  constexpr float threshold = 1.0e-35f;
  if (out_length > threshold) {
    out_length = std::sqrt(out_length);
    return v / out_length;
  }
  return float3(0.0f);
}
}  // namespace math
namespace bke::mesh {
struct CornerNormalSpace {
  float3 vec_lnor, vec_ref, vec_ortho;
  float ref_alpha, ref_beta;
};
}  // namespace bke::mesh
}  // namespace blender

// Scalar support operations match their pinned math_vector_inline.c definitions.
MINLINE bool is_zero_v3(const float v[3])
{
  return (v[0] == 0.0f && v[1] == 0.0f && v[2] == 0.0f);
}
MINLINE int compare_ff(float a, float b, const float max_diff)
{
  return fabsf(a - b) <= max_diff;
}
MINLINE bool compare_v3v3(const float v1[3], const float v2[3], const float limit)
{
  return (compare_ff(v1[0], v2[0], limit) && compare_ff(v1[1], v2[1], limit) &&
          compare_ff(v1[2], v2[2], limit));
}
MINLINE void mul_v3_v3fl(float r[3], const float a[3], float f)
{
  r[0] = a[0] * f;
  r[1] = a[1] * f;
  r[2] = a[2] * f;
}
MINLINE void madd_v3_v3fl(float r[3], const float a[3], float f)
{
  r[0] += a[0] * f;
  r[1] += a[1] * f;
  r[2] += a[2] * f;
}

#include "codec_exact.inc"

using blender::float3;
using blender::short2;
using blender::bke::mesh::CornerNormalSpace;

static bool finite(const float3 &v)
{
  return std::isfinite(v[0]) && std::isfinite(v[1]) && std::isfinite(v[2]);
}
static float3 cross(const float3 &a, const float3 &b)
{
  return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0]};
}
static std::string frame_error(const CornerNormalSpace &s, bool invalid_range_fallback)
{
  const auto vectors = std::array<float3, 3>{s.vec_lnor, s.vec_ref, s.vec_ortho};
  for (const auto &v : vectors) {
    if (!finite(v)) return "frame_nonfinite";
    if (std::abs(blender::math::dot(v, v) - 1.0f) > 2e-6f) return "frame_not_unit";
  }
  for (int i = 0; i < 3; i++) {
    for (int j = i + 1; j < 3; j++) {
      if (std::abs(blender::math::dot(vectors[i], vectors[j])) > 2e-6f)
        return "frame_not_orthogonal";
    }
  }
  const auto expected = cross(s.vec_lnor, s.vec_ref);
  for (int i = 0; i < 3; i++) {
    if (std::abs(expected[i] - s.vec_ortho[i]) > 2e-6f) return "frame_not_right_handed";
  }
  if (!std::isfinite(s.ref_alpha) || !std::isfinite(s.ref_beta)) return "range_nonfinite";
  const bool zero_allowed = invalid_range_fallback &&
                            (s.ref_alpha == 0.0f || s.ref_beta == 0.0f);
  if (invalid_range_fallback && !zero_allowed) return "diagnostic_requires_zero_range";
  if (s.ref_alpha < 0.0f || s.ref_alpha > float(M_PI) || s.ref_beta < 0.0f ||
      s.ref_beta > float(M_PI * 2.0) ||
      (!zero_allowed && (s.ref_alpha == 0.0f || s.ref_beta == 0.0f)))
    return "range_out_of_domain";
  return "";
}
static void scalar(float value)
{
  if (std::isfinite(value)) std::cout << value;
  else std::cout << "null";
}
static void vector(const float3 &v)
{
  std::cout << '[';
  for (int i = 0; i < 3; i++) {
    if (i) std::cout << ',';
    scalar(v[i]);
  }
  std::cout << ']';
}
static int reject(const std::string &reason, bool input_normalization_executed = false)
{
  std::cout << "{\"status\":\"rejected\",\"reason\":\"" << reason
            << "\",\"codecEncoderExecuted\":false,\"codecDecoderExecuted\":false,"
            << "\"inputNormalizationExecuted\":" << input_normalization_executed << "}\n";
  return 0;
}
static float number(const char *value)
{
  char *end;
  const float result = std::strtof(value, &end);
  if (!*value || *end) throw std::runtime_error("malformed_number");
  return result;
}

int main(int argc, char **argv)
{
  static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559);
  static_assert(sizeof(short) == 2 && SHRT_MAX == 32767);
  std::cout << std::setprecision(17) << std::boolalpha;
  if (std::fesetround(FE_TONEAREST) != 0 || std::fegetround() != FE_TONEAREST)
    return reject("floating_point_environment_unavailable");
  if (argc == 2 && std::string(argv[1]) == "--environment") {
    volatile float subnormal = std::numeric_limits<float>::denorm_min();
    volatile float factor = 2.0f;
    const float arithmetic_subnormal = subnormal * factor;
    std::cout << "{\"floatBytes\":" << sizeof(float) << ",\"shortMax\":" << SHRT_MAX
              << ",\"FLT_EVAL_METHOD\":" << FLT_EVAL_METHOD
              << ",\"roundingMode\":\"FE_TONEAREST\",\"roundingModeVerified\":true,"
              << "\"float32SubnormalParsingPreserved\":"
              << (std::strtof("1e-40", nullptr) != 0.0f)
              << ",\"float32SubnormalArithmeticPreserved\":"
              << (arithmetic_subnormal == 2.0f * std::numeric_limits<float>::denorm_min())
              << "}\n";
    return 0;
  }
  if (argc != 20) return reject("invalid_argument_count");
  try {
    const std::string op = argv[1], mode = argv[2];
    float v[17];
    for (int i = 0; i < 17; i++) v[i] = number(argv[i + 3]);
    const CornerNormalSpace s{{v[0], v[1], v[2]}, {v[3], v[4], v[5]},
                             {v[6], v[7], v[8]}, v[9], v[10]};
    const float3 original{v[11], v[12], v[13]};
    if (op == "quantize") {
      if (!std::isfinite(v[16])) return reject("value_nonfinite");
      if (v[16] < -1.0f || v[16] > 1.0f) return reject("value_out_of_domain");
      const short encoded = unit_float_to_short(v[16]);
      std::cout << "{\"status\":\"accepted\",\"valueFloat32\":" << v[16]
                << ",\"scaled\":" << v[16] * float(SHRT_MAX)
                << ",\"shifted\":" << v[16] * float(SHRT_MAX) + 0.5f
                << ",\"encoded\":" << encoded
                << ",\"decodedFraction\":" << unit_short_to_float(encoded) << "}\n";
      return 0;
    }
    if (op == "acos") {
      if (!std::isfinite(v[16])) return reject("value_nonfinite");
      std::cout << "{\"status\":\"accepted\",\"valueFloat32\":" << v[16]
                << ",\"approximate\":" << blender::math::safe_acos_approx(v[16])
                << ",\"exactDoubleReference\":"
                << std::acos(std::clamp(double(v[16]), -1.0, 1.0)) << "}\n";
      return 0;
    }
    if (op == "normalize") {
      if (!finite(original)) return reject("normal_nonfinite");
      const auto normalized = blender::math::normalize(original);
      std::cout << "{\"status\":\"accepted\",\"normalInputFloat32\":";
      vector(original);
      std::cout << ",\"squaredLengthFloat32\":";
      scalar(blender::math::dot(original, original));
      std::cout << ",\"normalizedInput\":";
      vector(normalized);
      std::cout << ",\"normalizationCollapsed\":" << is_zero_v3(normalized) << "}\n";
      return 0;
    }
    if (op != "roundtrip" && op != "decode") return reject("unknown_operation");
    if (mode != "strict" && mode != "unit" && mode != "zero-sentinel" &&
        mode != "invalid-range-fallback") return reject("unknown_mode");
    if (mode == "invalid-range-fallback" && op != "decode")
      return reject("invalid_range_diagnostic_decode_only");
    const auto error = frame_error(s, mode == "invalid-range-fallback");
    if (!error.empty()) return reject(error);
    if (op == "decode") {
      for (int i = 14; i <= 15; i++) {
        if (!std::isfinite(v[i]) || v[i] != std::floor(v[i]) || v[i] < -32768 || v[i] > 32767)
          return reject("short_out_of_domain");
      }
      const short2 code{short(v[14]), short(v[15])};
      const auto decoded = blender::bke::mesh::corner_space_custom_data_to_normal(s, code);
      std::cout << "{\"status\":\"accepted\",\"encoded\":[" << code[0] << ',' << code[1]
                << "],\"decoded\":";
      vector(decoded);
      std::cout << ",\"upstreamFallback\":"
                << (code[0] == 0 || s.ref_alpha == 0 || s.ref_beta == 0) << "}\n";
      return 0;
    }
    if (!finite(original)) return reject("normal_nonfinite");
    const bool zero = is_zero_v3(original);
    if (mode == "zero-sentinel" && !zero) return reject("diagnostic_requires_zero_normal");
    if (zero && mode != "zero-sentinel") return reject("normal_zero");
    float3 normal = original;
    if (mode == "strict") {
      normal = blender::math::normalize(original);
      if (!finite(normal) || is_zero_v3(normal)) return reject("normal_collapsed_by_upstream_normalize", true);
    }
    if (mode != "zero-sentinel" &&
        std::abs(blender::math::dot(normal, normal) - 1.0f) > 2e-6f)
      return reject("normal_not_unit", mode == "strict");
    const auto code = blender::bke::mesh::corner_space_custom_normal_to_data(s, normal);
    const auto decoded = blender::bke::mesh::corner_space_custom_data_to_normal(s, code);
    const bool near_auto = compare_v3v3(s.vec_lnor, normal, 1e-4f);
    std::cout << "{\"status\":\"accepted\",\"normalInputFloat32\":";
    vector(original);
    std::cout << ",\"normalizedInput\":";
    vector(normal);
    std::cout << ",\"encoded\":[" << code[0] << ',' << code[1] << "],\"decoded\":";
    vector(decoded);
    std::cout << ",\"trace\":{\"nearAuto\":" << near_auto << ",\"zeroSentinel\":" << zero;
    if (!zero && !near_auto) {
      const float pi2 = float(M_PI * 2.0);
      const float cos_alpha = blender::math::dot(s.vec_lnor, normal);
      const float alpha = blender::math::safe_acos_approx(cos_alpha);
      const float3 projected = blender::math::normalize(s.vec_lnor * -cos_alpha + normal);
      const float cos_beta = blender::math::dot(s.vec_ref, projected);
      const bool shortcut = !(cos_beta < LNOR_SPACE_TRIGO_THRESHOLD);
      float beta = blender::math::safe_acos_approx(cos_beta);
      if (blender::math::dot(s.vec_ortho, projected) < 0.0f) beta = pi2 - beta;
      const float af = alpha > s.ref_alpha ? -(pi2 - alpha) / (pi2 - s.ref_alpha) : alpha / s.ref_alpha;
      const float bf = shortcut ? 0.0f : (beta > s.ref_beta ? -(pi2 - beta) / (pi2 - s.ref_beta) : beta / s.ref_beta);
      std::cout << ",\"cosAlpha\":" << cos_alpha << ",\"alpha\":" << alpha
                << ",\"cosBeta\":" << cos_beta << ",\"azimuthShortcut\":" << shortcut
                << ",\"alphaFactor\":" << af << ",\"betaFactor\":" << bf
                << ",\"azimuthThresholdFloat32\":" << LNOR_SPACE_TRIGO_THRESHOLD
                << ",\"projectionCollapsed\":" << is_zero_v3(projected);
    }
    std::cout << "}}\n";
    return 0;
  }
  catch (const std::exception &) {
    return reject("malformed_number");
  }
}
