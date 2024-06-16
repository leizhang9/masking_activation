library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.prim_ops_pkg.all;

package mask_util_pkg is

	constant L_c : positive := 32;
	constant D_c : positive := 2;
	constant fp_fractional_bits_c : positive := 6;

	function masked_mvi(  
		a : integer
	) return std_ulogic_vector;

	function masked_mov(  
		x : std_ulogic_vector
	) return std_ulogic_vector;

	function mask_a(  
		a : std_ulogic_vector;
		rnd : std_logic_vector
	) return std_ulogic_vector;

	-- for simulation --
	function mask_val(
		a : std_logic_vector; 
		rnd : std_logic_vector
	) return std_logic_vector;

	function convert_real_to_fp(
		val : real
	) return std_ulogic_vector;

	function convert_fp_to_real(
		val : std_ulogic_vector
	) return real;

	function bool_truncation_sim(
		a_share_i : std_ulogic_vector
	) return std_ulogic_vector;

end package mask_util_pkg;

package body mask_util_pkg is

	function masked_mvi(
		a : integer
	) return std_ulogic_vector is

		variable b : std_ulogic_vector(L_c * D_c - 1 downto 0);

	begin

		b(L_c * 2 - 1 downto L_c * (2 - 1)) := std_logic_vector(to_unsigned(a, L_c));
		b(L_c * (2 - 1) - 1 downto 0) := PLSHIFT(std_logic_vector(to_unsigned(1, L_c)), (L_c - 1));
		b(L_c * 2 - 1 downto L_c * (2 - 1)) := PADD(b(L_c * 2 - 1 downto L_c * (2 - 1)), twos_complement(b(L_c * (2 - 1) - 1 downto 0)));

		return b;
		
	end function;

	function masked_mov(
		x : std_ulogic_vector
	) return std_ulogic_vector is

		variable temp : std_ulogic_vector(L_c * D_c - 1 downto 0);
	begin
		for i in 0 to D_c - 1 loop
			temp(L_c * (i + 1) - 1 downto L_c * i) := x(L_c * (i + 1) - 1 downto L_c * i);
		end loop;
		return temp;
	end function;

	function mask_a(
		a : std_ulogic_vector;
		rnd : std_ulogic_vector
	) return std_ulogic_vector is

		variable temp : std_ulogic_vector(L_c * D_c - 1 downto 0);
	begin

		temp(L_c * D_c - 1 downto L_c * (D_c - 1)) := a;

		for i in 0 to D_c - 2 loop
			temp(L_c * (i + 1) - 1 downto L_c * i) := rnd(L_c * (i + 1) - 1 downto L_c * i);
			temp(L_c * D_c - 1 downto L_c * (D_c - 1)) := PADD(
				temp(L_c * D_c - 1 downto L_c * (D_c - 1)), 
				twos_complement(temp(L_c * (i + 1) - 1 downto L_c * i))
			);
		end loop;
		return temp;
	end function;

	-- for simulation --
	function mask_val(
		a : std_logic_vector; 
		rnd : std_logic_vector
	) return std_logic_vector is
		variable temp : std_ulogic_vector(a'length * 2 - 1 downto 0);
	begin
		temp(a'length - 1 downto 0) := rnd;
		temp(a'length * 2 - 1 downto a'length) := PADD(a, twos_complement(rnd));
		return temp;
	end function;

	function convert_real_to_fp(
		val : real
	) return std_ulogic_vector is
		variable temp : std_ulogic_vector(L_c - 1 downto 0);
	begin
		temp := std_ulogic_vector(to_signed(integer(val * real(2**fp_fractional_bits_c)), L_c));
		return temp;
	end function;

	function convert_fp_to_real(
		val : std_ulogic_vector
	) return real is
		variable temp : real;
	begin
		temp := real(to_integer(signed(val))) / real(2**fp_fractional_bits_c) ;
		return temp;
	end function;

	function bool_truncation_sim(
		a_share_i : std_ulogic_vector
	) return std_ulogic_vector is
		variable a0        : std_ulogic_vector (L_c - 1 downto 0);
		variable a1        : std_ulogic_vector (L_c - 1 downto 0);
		variable gamma     : std_ulogic_vector (L_c - 1 downto 0) := (others=>'1');
		variable rnd       : std_ulogic_vector (L_c - 1 downto 0) := (others=>'1');
		variable tau       : std_ulogic_vector (L_c - 1 downto 0);
		variable b0        : std_ulogic_vector (L_c - 1 downto 0);
		variable b1        : std_ulogic_vector (L_c - 1 downto 0);
		variable omega     : std_ulogic_vector (L_c - 1 downto 0);
		variable b_share   : std_ulogic_vector (L_c * D_c - 1 downto 0);
		variable b_share_t : std_ulogic_vector (L_c * D_c - 1 downto 0);
		variable a_share_o : std_ulogic_vector (L_c * D_c - 1 downto 0);
	begin
		a0 := PADD(a_share_i(31 downto 0), rnd);
		a1 := PADD(a_share_i(63 downto 32), twos_complement(rnd));

		tau := std_ulogic_vector(shift_left(unsigned(gamma), 1)); 
		b1 := PXOR(gamma, a0);	
		omega := PAND(gamma, b1);
		b1 := PXOR(tau, a1);
		gamma := PXOR(gamma, b1);
		gamma := PAND(gamma, a0);
		omega := PXOR(omega, gamma);
		gamma := PAND(tau, a1);
		omega := PXOR(omega, gamma);

		for i in 0 to L_c - 1 loop
			gamma := PAND(tau, a0);
			gamma := PXOR(gamma, omega);
			tau := PAND(tau, a1);
			gamma := PXOR(gamma, tau);
			tau := std_ulogic_vector(shift_left(unsigned(gamma), 1));
		end loop;

		b1 := PXOR(b1, tau);
		b0 := a0;
		
		b_share := b1 & b0;
		
		for i in 0 to D_c - 1 loop
			b_share_t(L_c * (i + 1) - 1 downto L_c * i) := (L_c - 1 downto L_c - fp_fractional_bits_c => b_share(L_c * (i + 1) - 1)) 
				& (b_share(L_c * (i + 1) - 1 downto (L_c * i) + fp_fractional_bits_c));
		end loop;

		b0 := PXOR(b_share_t(31 downto 0), rnd);
		b1 := PXOR(b_share_t(63 downto 32), rnd);

		tau := PXOR(b1, gamma);
		tau := PADD(tau, twos_complement(gamma));
		tau := PXOR(tau, b1);

		gamma := PXOR(gamma, b0);
		a1 := PXOR(b1, gamma);
		a1 := PADD(a1, twos_complement(gamma));
		a1 := PXOR(a1, tau);
		a0 := b0;
		
		a_share_o := a1 & a0;

		return a_share_o;

	end function;

end package body;
