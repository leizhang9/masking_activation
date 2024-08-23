library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package prim_ops_pkg is

	function PADD(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector;

	function PMUL(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector;

	function PRSHIFT(  
		x : std_ulogic_vector;
		y : positive
	) return std_ulogic_vector;

	function PLSHIFT(  
		x : std_ulogic_vector;
		y : positive
	) return std_ulogic_vector;

	function PXOR(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector;

	function PAND(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector;

	function twos_complement(  
		x : std_ulogic_vector
	) return std_ulogic_vector;

end package prim_ops_pkg;

package body prim_ops_pkg is
	function PADD(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector is
		
		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(unsigned(x) + unsigned(y));
		return temp;
	end function;

	function PMUL(
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector is

		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(resize(unsigned(x) * unsigned(y), x'length));
		return temp;
	end function;

	function PRSHIFT(
		x : std_ulogic_vector;
		y : positive
	) return std_ulogic_vector is

		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(shift_right(unsigned(x), y));
		return temp;
	end function;

	function PLSHIFT(
		x : std_ulogic_vector;
		y : positive
	) return std_ulogic_vector is

		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(shift_left(unsigned(x), y));
		return temp;
	end function;

	function PXOR(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector is
		
		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(unsigned(x) xor unsigned(y));
		return temp;
	end function;

	function PAND(  
		x : std_ulogic_vector;
		y : std_ulogic_vector
	) return std_ulogic_vector is
		
		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(unsigned(x) and unsigned(y));
		return temp;
	end function;

	function twos_complement(
		x : std_ulogic_vector
	) return std_ulogic_vector is

		variable temp : std_ulogic_vector(x'length - 1 downto 0);
	begin
		temp := std_ulogic_vector(not(unsigned(x)) + 1);
		return temp;
	end function;

end package body;